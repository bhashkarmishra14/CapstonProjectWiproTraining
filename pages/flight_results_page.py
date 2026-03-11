import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from pages.base_page import BasePage
from utilities.logger import get_logger
#Locators
class FlightResultsPage(BasePage):
    book_now_button = (By.XPATH, "//button[contains(normalize-space(),'Book Now')]")
    first_price = (By.XPATH, "((//button[contains(normalize-space(),'Book Now')])[1]/ancestor::div[1]//*[contains(normalize-space(),'USD')])[1]")
    sort_control = (By.XPATH, "//*[contains(normalize-space(),'Sort')]")
    no_flights_text = (By.XPATH, "//*[contains(normalize-space(),'No flights found')]")
    loading_text = (By.XPATH,"//*[contains(normalize-space(),'Loading from more suppliers') or contains(normalize-space(),'Searching flights from Suppliers') or contains(normalize-space(),'Searching Flights...')]",)
    # Sets up results page logger and shared wait helpers.
    def __init__(self, driver):
        super().__init__(driver)
        self.logger = get_logger(self.__class__.__name__)
    # Confirms results page is loaded (book-now or no-flight state).
    def verify_results(self):
        WebDriverWait(self.driver, 40).until(
            lambda d: "/flights/" in d.current_url
            or len(d.find_elements(*self.book_now_button)) > 0
            or len(d.find_elements(*self.no_flights_text)) > 0
        )
        return True
    # Reads first visible price text from results list.
    def get_price(self):
        prices = self.driver.find_elements(*self.first_price)
        if prices:
            text = prices[0].text.strip()
            self.logger.info("First result price: %s", text)
            return text
        return ""
    # Clicks a visible Book Now and waits for navigation.
    def click_book_now(self):
        current_url = self.driver.current_url
        end = time.time() + 45
        while time.time() < end:
            buttons = self.driver.find_elements(*self.book_now_button)
            for button in buttons:
                try:
                    if not button.is_displayed() or not button.is_enabled():
                        continue
                    ActionChains(self.driver).move_to_element(button).click(button).perform()
                    WebDriverWait(self.driver, 10).until(lambda d: d.current_url != current_url)
                    return
                except Exception:
                    continue
            time.sleep(1)
        raise TimeoutError("Could not click Book Now")
    # Returns True if at least one Book Now button is present.
    def has_book_now(self):
        return len(self.driver.find_elements(*self.book_now_button)) > 0
    # Returns True if no-flight message is shown.
    def has_no_flights(self):
        return len(self.driver.find_elements(*self.no_flights_text)) > 0
    # Validates sort/filter controls on results page.
    def validate_result_controls(self):
        self.wait.until(EC.visibility_of_element_located(self.sort_control))
        return True
    # Waits until inventory resolves to either flights or no-flights.
    def wait_for_inventory(self, timeout=300):
        end = time.time() + timeout
        while time.time() < end:
            if self.has_book_now():
                return
            if self.has_no_flights() and not self.driver.find_elements(*self.loading_text):
                return
            time.sleep(2)
        raise TimeoutError("Flight inventory did not finish loading")
