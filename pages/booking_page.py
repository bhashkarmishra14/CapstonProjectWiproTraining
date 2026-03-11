import os
import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from pages.base_page import BasePage
from utilities.logger import get_logger
# BookingPage Class
# This class handles everything related to the booking page.
# It fills passenger details, confirms booking and downloads the invoice.
class BookingPage(BasePage):
    # Locators
    # All the elements used in the booking page are defined here.
    booking_guest_radio = (By.ID, "booking_guest")
    guest_details_section = (By.XPATH, "//*[contains(normalize-space(),'Guest Details')]")
    guest_title_select = (By.XPATH, "//select[@x-model='primary_guest.title']")
    first_name_input = (By.XPATH, "//input[@x-model='primary_guest.first_name']")
    last_name_input = (By.XPATH, "//input[@x-model='primary_guest.last_name']")
    email_input = (By.XPATH, "//input[@x-model='primary_guest.email']")
    phone_input = (By.XPATH, "//input[@x-model='primary_guest.phone']")
    country_code_select = (By.XPATH, "//select[@x-model='primary_guest.country_code']")
    # checkbox used when booking ticket for someone else
    book_for_someone_checkbox = (By.XPATH,"//*[contains(normalize-space(),\"I'm booking for someone else\")]/preceding::input[@type='checkbox'][1]")
    # lead traveler section fields
    lead_title_select = (By.XPATH,"(//*[contains(normalize-space(),'Lead Traveler')]/following::label[contains(normalize-space(),'Title')]/following::select[1])[1]")
    nationality_select = (By.XPATH,"(//*[contains(normalize-space(),'Lead Traveler')]/following::label[contains(normalize-space(),'Nationality')]/following::select[1])[1]")
    dob_day_select = (By.XPATH,"(//*[contains(normalize-space(),'Lead Traveler')]/following::label[contains(normalize-space(),'Date of Birth')]/following::select[1])[1]")
    dob_month_select = (By.XPATH,"(//*[contains(normalize-space(),'Lead Traveler')]/following::label[contains(normalize-space(),'Date of Birth')]/following::select[2])[1]")
    dob_year_select = (By.XPATH,"(//*[contains(normalize-space(),'Lead Traveler')]/following::label[contains(normalize-space(),'Date of Birth')]/following::select[3])[1]")
    passport_input = (By.XPATH,"(//*[contains(normalize-space(),'Lead Traveler')]/following::label[contains(normalize-space(),'Passport')]/following::input[1])[1]")
    # payment related elements
    digital_wallet_button = (By.XPATH, "//div[normalize-space()='Digital Wallet']")
    terms_checkbox = (By.ID, "terms_accepted")
    confirm_button = (By.CSS_SELECTOR, "button[type='submit']")
    # used to check if invoice page is loaded
    invoice_details_marker = (By.XPATH, "//*[contains(normalize-space(),'Invoice Details')]")
    # button used to download invoice
    download_invoice_btn = (By.XPATH,"//div[@class='btn light w-full flex items-center justify-start gap-2 cursor-pointer']")
    # constructor
    # initializes driver and logger
    def __init__(self, driver):
        super().__init__(driver)
        self.logger = get_logger(self.__class__.__name__)
    # utility method
    # fetches required data from Excel test data
    # if value is missing it throws an error
    def _required_value(self, data, *keys):
        for key in keys:
            value = data.get(key)
            if value is not None and str(value).strip() != "":
                return str(value).strip()
        raise AssertionError(f"Missing required test data: one of {keys}")
    # selects dropdown value using visible text
    # if exact match fails it tries normalized comparison
    def _select_by_text(self, locator, value):
        element = self.wait.until(EC.visibility_of_element_located(locator))
        target = str(value).strip()
        select = Select(element)
        try:
            select.select_by_visible_text(target)
            return
        except Exception:
            pass
        normalized = target.lower().replace(".", "")
        for option in select.options:
            text = (option.text or "").strip().lower().replace(".", "")
            if text == normalized or normalized in text:
                option.click()
                return
        raise AssertionError(f"Could not select '{target}'")
    # simple helper to type text in input fields
    def _type(self, locator, value):
        element = self.wait.until(EC.visibility_of_element_located(locator))
        element.clear()
        element.send_keys(str(value).strip())
    # phone numbers from Excel sometimes appear in scientific notation
    # this method converts them into normal digits
    def _normalize_phone(self, value):
        raw = str(value).strip()
        if "E+" in raw.upper():
            try:
                raw = str(int(float(raw)))
            except Exception:
                pass
        digits = "".join(ch for ch in raw if ch.isdigit())
        return digits
    # makes sure booking form is visible and ready
    def validate_booking_controls(self):
        guest_radio = self.wait.until(EC.element_to_be_clickable(self.booking_guest_radio))
        if not guest_radio.is_selected():
            guest_radio.click()
        self.wait.until(EC.visibility_of_element_located(self.guest_details_section))
        self.wait.until(EC.visibility_of_element_located(self.first_name_input))
        return True
    # fills passenger details from Excel test data
    def fill_passenger_details(self, data):
        title = self._required_value(data, "title")
        first_name = self._required_value(data, "fname", "first_name")
        last_name = self._required_value(data, "lname", "last_name")
        email = self._required_value(data, "email")
        phone = self._normalize_phone(self._required_value(data, "phone"))
        country_code = self._required_value(data, "country_code")
        self._select_by_text(self.guest_title_select, title)
        self._select_by_text(self.country_code_select, country_code)
        self._type(self.first_name_input, first_name)
        self._type(self.last_name_input, last_name)
        self._type(self.email_input, email)
        self._type(self.phone_input, phone)
    # fills lead traveler details when booking for someone else
    def fill_lead_traveler_details(self, data):
        title = self._required_value(data, "title")
        nationality = self._required_value(data, "nationality")
        dob_day = self._required_value(data, "dob_day")
        dob_month = self._required_value(data, "dob_month")
        dob_year = self._required_value(data, "dob_year")
        passport = self._required_value(data, "passport")
        checkbox = self.wait.until(EC.element_to_be_clickable(self.book_for_someone_checkbox))
        if not checkbox.is_selected():
            ActionChains(self.driver).move_to_element(checkbox).click(checkbox).perform()
        self._select_by_text(self.lead_title_select, title)
        self._select_by_text(self.nationality_select, nationality)
        self._select_by_text(self.dob_day_select, dob_day)
        self._select_by_text(self.dob_month_select, dob_month)
        self._select_by_text(self.dob_year_select, dob_year)
        self._type(self.passport_input, passport)
    # selects Digital Wallet payment option
    def digital_wallet(self):
        button = self.wait.until(EC.element_to_be_clickable(self.digital_wallet_button))
        if button.is_selected():
            return True
        button.click()
        return True
    # accepts terms and conditions checkbox
    def agree_terms(self):
        checkbox = self.wait.until(EC.element_to_be_clickable(self.terms_checkbox))
        if not checkbox.is_selected():
            try:
                checkbox.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", checkbox)
            time.sleep(0.3)
        assert checkbox.is_selected(), "Unable to select Terms and Conditions"
    # clicks confirm booking button
    def confirm_booking(self):
        button = self.wait.until(EC.element_to_be_clickable(self.confirm_button))
        button.click()
        return True
    # after booking confirmation the invoice page opens
    # this method waits for that page and clicks download invoice button
    def wait_then_download_invoice(self):
        # wait until invoice page loads
        self.wait.until(
            lambda d: "/invoice/" in d.current_url.lower()
        )
        self.logger.info("Invoice page loaded")
        download_btn = self.wait.until(
            EC.element_to_be_clickable(self.download_invoice_btn)
        )
        download_btn.click()
        self.logger.info("Download invoice button clicked")
        # small wait for file download
        time.sleep(5)
        project_root = os.getcwd()
        invoice_folder = os.path.join(project_root, "reports", "invoices")
        self.logger.info(f"Invoice downloaded inside: {invoice_folder}")
        return invoice_folder