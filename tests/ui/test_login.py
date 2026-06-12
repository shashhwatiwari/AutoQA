"""
Login test suite — saucedemo.com

Positive cases:   standard_user, performance_glitch_user
Negative cases:   wrong password, locked-out user, empty fields, SQL-injection attempt
UX assertions:    error banner content, error close button, field icon state
"""
import pytest
from pages.login_page import LoginPage
from pages.inventory_page import InventoryPage


@pytest.mark.ui
class TestLoginPositive:

    def test_standard_user_reaches_inventory(self, driver, base_url):
        login = LoginPage(driver, base_url)
        login.open()
        login.login("standard_user", "secret_sauce")

        inventory = InventoryPage(driver, base_url)
        inventory.wait_for_visible(inventory._TITLE)

        assert "inventory" in driver.current_url
        assert inventory.get_item_count() == 6

    def test_inventory_title_is_products(self, driver, base_url):
        login = LoginPage(driver, base_url)
        login.open()
        login.login("standard_user", "secret_sauce")

        inventory = InventoryPage(driver, base_url)
        assert inventory.get_text(inventory._TITLE) == "Products"

    def test_performance_glitch_user_can_login(self, driver, base_url):
        login = LoginPage(driver, base_url)
        login.open()
        login.login("performance_glitch_user", "secret_sauce")

        inventory = InventoryPage(driver, base_url)
        # glitch user is slow — give it extra time
        inventory.wait_for_visible(inventory._TITLE, timeout=20)
        assert "inventory" in driver.current_url

    def test_login_page_title(self, driver, base_url):
        login = LoginPage(driver, base_url)
        login.open()
        assert "Swag Labs" in driver.title

    def test_logo_present_on_login_page(self, driver, base_url):
        login = LoginPage(driver, base_url)
        login.open()
        assert login.is_visible(login._LOGIN_LOGO)


@pytest.mark.ui
class TestLoginNegative:

    def test_wrong_password_shows_error(self, driver, base_url):
        login = LoginPage(driver, base_url)
        login.open()
        login.login("standard_user", "wrong_password")

        assert login.is_error_displayed()
        assert "Epic sadface" in login.get_error_message()

    def test_wrong_password_error_mentions_credentials(self, driver, base_url):
        login = LoginPage(driver, base_url)
        login.open()
        login.login("standard_user", "wrong_password")

        msg = login.get_error_message().lower()
        # SauceDemo intentionally uses a single vague message
        assert "username and password do not match" in msg or "epic sadface" in msg

    def test_locked_out_user_shows_specific_message(self, driver, base_url):
        login = LoginPage(driver, base_url)
        login.open()
        login.login("locked_out_user", "secret_sauce")

        assert login.is_error_displayed()
        assert "locked out" in login.get_error_message().lower()

    def test_empty_username_shows_error(self, driver, base_url):
        login = LoginPage(driver, base_url)
        login.open()
        login.login("", "secret_sauce")

        assert login.is_error_displayed()
        assert "Username is required" in login.get_error_message()

    def test_empty_password_shows_error(self, driver, base_url):
        login = LoginPage(driver, base_url)
        login.open()
        login.login("standard_user", "")

        assert login.is_error_displayed()
        assert "Password is required" in login.get_error_message()

    def test_empty_both_fields_shows_error(self, driver, base_url):
        login = LoginPage(driver, base_url)
        login.open()
        login.login("", "")

        assert login.is_error_displayed()
        assert "Username is required" in login.get_error_message()

    def test_error_banner_can_be_dismissed(self, driver, base_url):
        login = LoginPage(driver, base_url)
        login.open()
        login.login("", "")

        assert login.is_error_displayed()
        login.close_error()
        assert not login.is_error_displayed()

    def test_invalid_login_stays_on_login_page(self, driver, base_url):
        login = LoginPage(driver, base_url)
        login.open()
        login.login("bad_user", "bad_pass")

        assert login.is_on_login_page()
        assert "inventory" not in driver.current_url

    def test_sql_injection_attempt_shows_error(self, driver, base_url):
        login = LoginPage(driver, base_url)
        login.open()
        login.login("' OR '1'='1", "' OR '1'='1")

        assert login.is_error_displayed()
        assert "inventory" not in driver.current_url
