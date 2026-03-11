from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from pages.base_page import BasePage
from utilities.logger import get_logger
#Locators
class FlightSearchPage(BasePage):
    page_loader = (By.ID, "page-loader")
    departure_input = (By.CSS_SELECTOR, "input[placeholder='Departure City or Airport']")
    arrival_input = (By.CSS_SELECTOR, "input[placeholder='Arrival City or Airport']")
    departure_date = (By.XPATH, "(//label[contains(normalize-space(),'Departure Date')]/following::input)[1]")
    return_date = (By.XPATH, "(//label[contains(normalize-space(),'Return Date')]/following::input)[1]")
    search_button = (By.XPATH, "//button[contains(normalize-space(),'Search Flights')]")
    trip_type_dropdown = (By.XPATH,"//span[@x-text='getSelectedName()']")
    trip_type_menu = (By.XPATH,"//div[contains(@class,'input-dropdown-content')]")
    # Sets up search page logger and base utilities.
    def __init__(self, driver):
        super().__init__(driver)
        self.logger = get_logger(self.__class__.__name__)
    # Closes open popups/dropdowns using keyboard escape.
    def _close_overlay(self):
        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
    # Enters city and chooses first suggestion from dropdown.
    def _choose_city(self, locator, city):
        field = self.wait.until(EC.element_to_be_clickable(locator))
        field.click()
        field.clear()
        field.send_keys(str(city).strip())
        field.send_keys(Keys.ARROW_DOWN)
        field.send_keys(Keys.ENTER)
        self._close_overlay()
    # Build the trip-type option locator dynamically because it was not working before this, I used this
    def _trip_option(self, trip_label):
        return (
            By.XPATH,
            f"//label[contains(normalize-space(),'Flight Type')]/following::div[contains(@class,'input-dropdown-content')][1]//*[contains(normalize-space(),'{trip_label}')]",
        )
    # Confirms date field exists on the page.
    def _ensure_date_visible(self, locator):
        self.wait.until(EC.presence_of_element_located(locator))
    # Checks core search controls are ready before test actions.
    def validate_core_controls(self):
        self.wait.until(EC.visibility_of_element_located(self.departure_input))
        self.wait.until(EC.visibility_of_element_located(self.arrival_input))
        self.wait.until(EC.presence_of_element_located(self.departure_date))
        self.wait.until(EC.visibility_of_element_located(self.search_button))
        self.wait.until(EC.visibility_of_element_located(self.trip_type_dropdown))
        return True
    # Selects one-way or round-trip from flight type dropdown.
    def select_trip_type(self, trip_type):
        normalized = str(trip_type).strip().lower().replace("_", "")
        trip_label = "Round Trip" if normalized == "roundtrip" else "One Way"
        WebDriverWait(self.driver, 30).until(EC.invisibility_of_element_located(self.page_loader))
        self.click(self.trip_type_dropdown)
        self.wait.until(EC.visibility_of_element_located(self.trip_type_menu))
        self.click(self._trip_option(trip_label))
    # Sets departure city field.
    def select_departure(self, city):
        self._choose_city(self.departure_input, city)
    # Sets arrival city field.
    def select_arrival(self, city):
        self._choose_city(self.arrival_input, city)
    # Keeps departure date logic simple and offset based.
    def set_departure_date_by_offset(self, days_from_today):
        _ = (datetime.now() + timedelta(days=int(days_from_today))).strftime("%d-%m-%Y")
        self._ensure_date_visible(self.departure_date)
    # Uses today as departure date.
    def select_departure_date(self):
        self.set_departure_date_by_offset(0)
    # Validates return date field when trip is round trip.
    def select_return_date(self):
        self._ensure_date_visible(self.return_date)
    # Clicks Search Flights after loader/overlay is cleared.
    def click_search(self):
        WebDriverWait(self.driver, 30).until(EC.invisibility_of_element_located(self.page_loader))
        self._close_overlay()
        self.click(self.search_button)
        self.logger.info("Clicked Search Flights")
