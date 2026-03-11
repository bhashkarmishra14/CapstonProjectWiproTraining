from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
class BasePage:
    # Stores shared driver and wait utility for all pages.
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)
    def click(self, locator):
        element = self.wait.until(EC.presence_of_element_located(locator))
        # scroll element into view
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        try:
            self.wait.until(EC.element_to_be_clickable(locator)).click()
        except Exception:
            # fallback click if intercepted
            self.driver.execute_script("arguments[0].click();", element)
    # Returns True when an element is visible.
    def is_visible(self, locator):
        return self.wait.until(EC.visibility_of_element_located(locator)).is_displayed()
    # Clears and types text into a field.
    def type(self, locator, text):
        element = self.wait.until(EC.visibility_of_element_located(locator))
        element.clear()
        element.send_keys(text)
