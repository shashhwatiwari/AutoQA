import os
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://www.saucedemo.com")
API_BASE_URL = os.getenv("API_BASE_URL", "https://reqres.in/api")
INTERNET_BASE_URL = os.getenv("INTERNET_BASE_URL", "https://the-internet.herokuapp.com")


def pytest_addoption(parser):
    parser.addoption(
        "--headless",
        action="store_true",
        default=False,
        help="Run browser tests in headless mode",
    )
    parser.addoption(
        "--base-url",
        action="store",
        default=BASE_URL,
        help="Base URL for UI tests",
    )
    parser.addoption(
        "--api-base-url",
        action="store",
        default=API_BASE_URL,
        help="Base URL for API tests",
    )
    parser.addoption(
        "--internet-base-url",
        action="store",
        default=INTERNET_BASE_URL,
        help="Base URL for the-internet.herokuapp.com tests",
    )


@pytest.fixture(scope="session")
def base_url(request):
    return request.config.getoption("--base-url")


@pytest.fixture(scope="session")
def api_base_url(request):
    return request.config.getoption("--api-base-url")


@pytest.fixture(scope="session")
def internet_base_url(request):
    return request.config.getoption("--internet-base-url")


@pytest.fixture(scope="function")
def driver(request):
    opts = Options()

    # Always headless in CI; opt-in via --headless flag locally
    if request.config.getoption("--headless") or os.getenv("CI"):
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")

    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-extensions")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    driver.implicitly_wait(10)

    yield driver

    driver.quit()


@pytest.fixture(scope="function")
def authenticated_driver(driver, base_url):
    """Driver pre-logged-in to SauceDemo as standard_user."""
    from pages.login_page import LoginPage

    page = LoginPage(driver, base_url)
    page.open()
    page.login("standard_user", "secret_sauce")
    yield driver
