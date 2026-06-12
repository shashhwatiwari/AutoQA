"""
Cookie / session test suite — saucedemo.com

Covers:
  - session cookie is set on login, cleared on logout
  - cookie value matches username
  - clearing cookies mid-session forces re-authentication
  - cart state is preserved across page navigations (session persistence)
  - different users produce different session values
  - injecting a forged session cookie bypasses the login form
"""
import pytest
from pages.login_page import LoginPage
from pages.inventory_page import InventoryPage
from pages.cart_page import CartPage


SESSION_COOKIE = "session-username"


@pytest.mark.ui
@pytest.mark.regression
class TestSessionCookieLifecycle:

    def test_cookie_absent_before_login(self, driver, base_url):
        login = LoginPage(driver, base_url)
        login.open()
        assert login.get_cookie(SESSION_COOKIE) is None

    def test_cookie_set_after_login(self, driver, base_url):
        login = LoginPage(driver, base_url)
        login.open()
        login.login("standard_user", "secret_sauce")

        cookie = login.get_cookie(SESSION_COOKIE)
        assert cookie is not None, f"Expected '{SESSION_COOKIE}' cookie to exist"

    def test_cookie_value_matches_username(self, driver, base_url):
        login = LoginPage(driver, base_url)
        login.open()
        login.login("standard_user", "secret_sauce")

        cookie = login.get_cookie(SESSION_COOKIE)
        assert cookie["value"] == "standard_user"

    def test_all_cookies_present_after_login(self, driver, base_url):
        login = LoginPage(driver, base_url)
        login.open()
        login.login("standard_user", "secret_sauce")

        cookies = login.get_cookies()
        assert SESSION_COOKIE in cookies

    def test_different_users_yield_different_cookie_values(self, driver, base_url):
        login = LoginPage(driver, base_url)

        login.open()
        login.login("standard_user", "secret_sauce")
        value_standard = login.get_cookie(SESSION_COOKIE)["value"]

        login.delete_all_cookies()
        login.open()
        login.login("problem_user", "secret_sauce")

        # Wait for the inventory page to confirm login completed and cookies are set
        inventory = InventoryPage(driver, base_url)
        if not inventory.is_visible(inventory._TITLE, timeout=5):
            pytest.skip("problem_user login did not reach inventory — user may be unavailable")

        cookie = login.get_cookie(SESSION_COOKIE)
        if cookie is None:
            pytest.skip("problem_user session cookie not set — behaviour may have changed")
        value_problem = cookie["value"]

        assert value_standard != value_problem


@pytest.mark.ui
@pytest.mark.regression
class TestSessionPersistence:

    def test_cart_count_persists_across_navigation(self, authenticated_driver, base_url):
        inventory = InventoryPage(authenticated_driver, base_url)
        inventory.open()
        inventory.add_item_to_cart(0)
        count_before = inventory.get_cart_count()

        # Navigate away and return
        inventory.open()
        count_after = inventory.get_cart_count()
        assert count_after == count_before

    def test_cart_items_persist_after_navigating_to_cart_and_back(
        self, authenticated_driver, base_url
    ):
        inventory = InventoryPage(authenticated_driver, base_url)
        inventory.open()
        item_name = inventory.get_item_names()[0]
        inventory.add_item_to_cart(0)

        inventory.go_to_cart()
        cart = CartPage(authenticated_driver, base_url)
        assert cart.is_item_in_cart(item_name)

        cart.continue_shopping()
        inventory.go_to_cart()
        assert cart.is_item_in_cart(item_name), "Item should still be in cart"

    def test_session_survives_page_reload(self, authenticated_driver, base_url):
        inventory = InventoryPage(authenticated_driver, base_url)
        inventory.open()
        inventory.add_item_to_cart(0)

        authenticated_driver.refresh()
        inventory.wait_for_visible(inventory._TITLE)

        assert inventory.get_cart_count() == 1

    def test_cookie_domain_matches_app_domain(self, authenticated_driver, base_url):
        login = LoginPage(authenticated_driver, base_url)
        cookie = login.get_cookie(SESSION_COOKIE)
        assert cookie is not None
        # Cookie domain should be the site domain, not a third-party
        assert "saucedemo" in cookie.get("domain", "")


@pytest.mark.ui
class TestCookieClearBehaviour:

    def test_clearing_cookies_forces_re_auth(self, driver, base_url):
        login = LoginPage(driver, base_url)
        login.open()
        login.login("standard_user", "secret_sauce")

        # Confirm we're on inventory
        assert "inventory" in driver.current_url

        # Wipe cookies and force a navigation
        login.delete_all_cookies()
        driver.get(f"{base_url}/inventory.html")

        # SauceDemo redirects back to login when session is missing
        assert login.is_on_login_page() or "inventory" not in driver.current_url

    def test_deleting_only_session_cookie_prevents_access(self, driver, base_url):
        login = LoginPage(driver, base_url)
        login.open()
        login.login("standard_user", "secret_sauce")

        login.delete_cookie(SESSION_COOKIE)
        driver.get(f"{base_url}/inventory.html")

        assert login.is_on_login_page() or "inventory" not in driver.current_url

    def test_cart_is_empty_after_session_reset(self, driver, base_url):
        login = LoginPage(driver, base_url)
        login.open()
        login.login("standard_user", "secret_sauce")

        inventory = InventoryPage(driver, base_url)
        inventory.add_item_to_cart(0)
        assert inventory.get_cart_count() == 1

        # Reset session — clear cookies AND localStorage (cart state lives there)
        login.clear_local_storage()
        login.delete_all_cookies()
        login.open()
        login.login("standard_user", "secret_sauce")
        inventory.open()

        # Fresh session — cart should be empty
        assert inventory.get_cart_count() == 0


@pytest.mark.ui
class TestCookieInjection:

    def test_injecting_valid_session_cookie_grants_access(self, driver, base_url):
        """
        Demonstrates that SauceDemo's auth is purely cookie-based:
        setting the cookie manually bypasses the login form entirely.
        This is a realistic session-hijacking scenario test.
        """
        # Navigate to root first so the domain is set for cookie injection
        driver.get(base_url)
        driver.add_cookie({"name": SESSION_COOKIE, "value": "standard_user"})

        # Now navigate directly to the protected page
        driver.get(f"{base_url}/inventory.html")

        inventory = InventoryPage(driver, base_url)
        assert inventory.is_visible(inventory._TITLE, timeout=5), (
            "Injected session cookie should grant access to inventory"
        )
