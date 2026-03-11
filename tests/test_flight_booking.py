import pytest
from pages.booking_page import BookingPage
from pages.flight_results_page import FlightResultsPage
from pages.flight_search_page import FlightSearchPage
from utilities.excel_reader import read_test_data
from utilities.logger import get_logger
logger = get_logger("test_flights")
# read data from Excel
test_data = read_test_data("testdata/flight_test_data.xlsx")
# filter test data
one_way_data = [
    row for row in test_data
    if str(row.get("trip_type", "")).strip().lower().replace("_", "") == "oneway"
]
round_trip_data = [
    row for row in test_data
    if str(row.get("trip_type", "")).strip().lower().replace("_", "") == "roundtrip"
]
# helper method to fetch required values from excel row
def required(data, key):
    value = data.get(key)
    assert value is not None and str(value).strip() != "", \
        f"Missing required '{key}' in Excel row: {data}"
    return value
# reusable search flow used by tests
def run_search(driver, data):
    search_page = FlightSearchPage(driver)
    # check if search controls are visible
    assert search_page.validate_core_controls()
    trip_type = str(required(data, "trip_type"))
    search_page.select_trip_type(trip_type)
    search_page.select_departure(required(data, "from_city"))
    search_page.select_arrival(required(data, "to_city"))
    search_page.select_departure_date()
    # return date only for roundtrip
    if trip_type.strip().lower().replace("_", "") == "roundtrip":
        search_page.select_return_date()
    search_page.click_search()
    results_page = FlightResultsPage(driver)
    assert results_page.verify_results()
    assert results_page.validate_result_controls()
    return results_page
#ONE WAY SEARCH TEST
@pytest.mark.skipif(not one_way_data, reason="No one-way rows found in Excel data")
@pytest.mark.parametrize("data", one_way_data)
def test_validate_one_way_search_controls(driver, data):
    logger.info("Validate one way search")
    results_page = run_search(driver, data)
    # validate results
    assert results_page.has_book_now() or results_page.has_no_flights()
#ROUND TRIP SEARCH TEST
@pytest.mark.skipif(not round_trip_data, reason="No round-trip rows found in Excel data")
@pytest.mark.parametrize("data", round_trip_data)
def test_validate_round_trip_search_controls(driver, data):
    logger.info("Validate round trip search")
    results_page = run_search(driver, data)
    # ensure roundtrip url
    assert "/roundtrip/" in driver.current_url, \
        f"Trip type is not roundtrip in URL: {driver.current_url}"
    assert results_page.has_book_now() or results_page.has_no_flights()
# FULL BOOKING FLOW
@pytest.mark.skipif(not round_trip_data, reason="No round-trip rows found in Excel data")
@pytest.mark.parametrize("data", round_trip_data)
def test_round_trip_booking_confirm(driver, data):
    logger.info("Start full booking flow")
    results_page = run_search(driver, data)
    assert "/roundtrip/" in driver.current_url, \
        f"Trip type is not roundtrip in URL: {driver.current_url}"
    # wait for flight inventory
    results_page.wait_for_inventory(timeout=300)
    assert results_page.has_book_now(), \
        "Book Now not available for this route/date"
    # capture first price
    results_page.get_price()
    # open booking page
    results_page.click_book_now()
    booking_page = BookingPage(driver)
    # validate booking page
    assert booking_page.validate_booking_controls()
    # fill passenger details
    booking_page.fill_passenger_details(data)
    # fill lead traveler details
    booking_page.fill_lead_traveler_details(data)
    # select pay later option
    assert booking_page.digital_wallet(), \
        "Digital Wallet option was not selected"
    # accept terms
    booking_page.agree_terms()
    # confirm booking
    assert booking_page.confirm_booking(), \
        "Confirm button was not clicked"
    # download invoice
    booking_page.wait_then_download_invoice()
    logger.info("Invoice download triggered successfully")