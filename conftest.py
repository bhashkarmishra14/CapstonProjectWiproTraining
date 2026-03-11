import os
from datetime import datetime
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
# Adds custom CLI flags for pytest runs
def pytest_addoption(parser):
    parser.addoption(
        "--keep-browser-open",
        action="store_true",
        default=False,
        help="Keep browser window open after test execution",
    )
@pytest.fixture
# Creates and returns a browser session for each test
def driver(request):
    project_root = os.getcwd()
    download_dir = os.path.join(project_root, "reports", "invoices")
    os.makedirs(download_dir, exist_ok=True)
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    # configure chrome download directory
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
    }
    options.add_experimental_option("prefs", prefs)
    browser = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )
    browser.get("https://phptravels.net/flights")
    WebDriverWait(browser, 60).until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "input[placeholder='Departure City or Airport']")
        )
    )
    yield browser
    if not request.config.getoption("--keep-browser-open"):
        browser.quit()
@pytest.hookimpl(hookwrapper=True)
# Captures screenshot automatically when a test fails
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)
    if report.when == "call" and report.failed:
        os.makedirs("reports/screenshots", exist_ok=True)
        name = datetime.now().strftime("%Y%m%d_%H%M%S")
        item.funcargs["driver"].save_screenshot(
            f"reports/screenshots/fail_{name}.png"
        )