"""
Regression smoke suite

Design goals
------------
smoke       — every test in this file also carries @pytest.mark.smoke.
              Running `pytest -m smoke` should finish in under 2 minutes and
              give a reliable YES/NO on whether all major system surfaces are
              alive. These tests are intentionally broad and shallow.

regression  — every test also carries @pytest.mark.regression, so the full
              regression run (`pytest -m regression`) automatically includes
              this suite alongside the deeper per-layer test files.

Surfaces covered (one assertion per surface — depth lives elsewhere):
  UI  — login page renders, login works, inventory loads, cart adds, checkout reachable
  BS4 — inventory HTML structure, login error present on bad credentials
  API — users list alive, user read schema, login returns token,
         register returns id+token, 404 on unknown user, 400 on bad auth
  Session — session cookie set on login
"""
import pytest

from pages.login_page import LoginPage
from pages.inventory_page import InventoryPage
from pages.cart_page import CartPage
from pages.checkout_page import CheckoutPage
from utils.api_client import APIClient, assert_status, get_json, assert_schema
import utils.parsing as p


VALID_USER = "standard_user"
VALID_PASS = "secret_sauce"
API_USER_SCHEMA = ["id", "email", "first_name", "last_name", "avatar"]


# ===========================================================================
# UI smoke — login & navigation
# ===========================================================================

@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.ui
class TestSmokeUI:

    def test_login_page_renders(self, driver, base_url):
        """Login form elements are present in the DOM."""
        login = LoginPage(driver, base_url)
        login.open()
        assert login.is_visible(login._LOGIN_BTN)
        assert login.is_visible(login._USERNAME)
        assert login.is_visible(login._PASSWORD)

    def test_valid_login_reaches_inventory(self, driver, base_url):
        login = LoginPage(driver, base_url)
        login.open()
        login.login(VALID_USER, VALID_PASS)
        InventoryPage(driver, base_url).wait_for_visible(
            InventoryPage(driver, base_url)._TITLE
        )
        assert "inventory" in driver.current_url

    def test_inventory_has_six_products(self, authenticated_driver, base_url):
        inventory = InventoryPage(authenticated_driver, base_url)
        inventory.open()
        assert inventory.get_item_count() == 6

    def test_add_to_cart_updates_badge(self, authenticated_driver, base_url):
        inventory = InventoryPage(authenticated_driver, base_url)
        inventory.open()
        inventory.add_item_to_cart(0)
        assert inventory.get_cart_count() == 1

    def test_cart_page_is_reachable(self, authenticated_driver, base_url):
        inventory = InventoryPage(authenticated_driver, base_url)
        inventory.open()
        inventory.go_to_cart()
        assert "cart" in authenticated_driver.current_url

    def test_checkout_step_one_is_reachable(self, authenticated_driver, base_url):
        inventory = InventoryPage(authenticated_driver, base_url)
        inventory.open()
        inventory.add_item_to_cart(0)
        inventory.go_to_cart()
        CartPage(authenticated_driver, base_url).proceed_to_checkout()
        assert "checkout-step-one" in authenticated_driver.current_url

    def test_invalid_login_shows_error(self, driver, base_url):
        login = LoginPage(driver, base_url)
        login.open()
        login.login("bad_user", "bad_pass")
        assert login.is_error_displayed()

    def test_session_cookie_set_on_login(self, driver, base_url):
        login = LoginPage(driver, base_url)
        login.open()
        login.login(VALID_USER, VALID_PASS)
        assert login.get_cookie("session-username") is not None


# ===========================================================================
# BS4 smoke — HTML structure after render
# ===========================================================================

@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.ui
class TestSmokeBS4:

    def test_login_form_structure_in_html(self, driver, base_url):
        """BS4 parses the static HTML and confirms form fields are present."""
        LoginPage(driver, base_url).open()
        p.assert_login_form_structure(driver.page_source)

    def test_password_field_is_masked(self, driver, base_url):
        LoginPage(driver, base_url).open()
        p.assert_password_field_is_masked(driver.page_source)

    def test_inventory_html_has_six_products(self, authenticated_driver, base_url):
        InventoryPage(authenticated_driver, base_url).open()
        p.assert_product_count(authenticated_driver.page_source, expected=6)

    def test_inventory_prices_are_positive(self, authenticated_driver, base_url):
        InventoryPage(authenticated_driver, base_url).open()
        p.assert_product_prices_are_positive(authenticated_driver.page_source)

    def test_login_error_present_in_html_after_bad_credentials(self, driver, base_url):
        login = LoginPage(driver, base_url)
        login.open()
        login.login("bad", "bad")
        p.assert_login_error_present(driver.page_source)

    def test_cart_link_in_inventory_html(self, authenticated_driver, base_url):
        InventoryPage(authenticated_driver, base_url).open()
        p.assert_cart_link_present(authenticated_driver.page_source)


# ===========================================================================
# API smoke — all endpoints alive and returning correct top-level shape
# ===========================================================================

@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.api
class TestSmokeAPI:

    def test_list_users_returns_200(self, api_base_url):
        resp = APIClient(api_base_url).get("/users")
        assert_status(resp, 200)

    def test_list_users_response_has_data_array(self, api_base_url):
        body = get_json(APIClient(api_base_url).get("/users"))
        assert isinstance(body.get("data"), list) and len(body["data"]) > 0

    def test_get_single_user_schema(self, api_base_url):
        body = get_json(APIClient(api_base_url).get("/users/2"))
        assert_schema(body["data"], API_USER_SCHEMA)

    def test_nonexistent_user_returns_404(self, api_base_url):
        assert_status(APIClient(api_base_url).get("/users/9999"), 404)

    def test_create_user_returns_201(self, api_base_url):
        resp = APIClient(api_base_url).post("/users", json={"name": "Smoke Bot", "job": "QA"})
        assert_status(resp, 201)

    def test_delete_user_returns_204(self, api_base_url):
        assert_status(APIClient(api_base_url).delete("/users/2"), 204)

    def test_login_returns_token(self, api_base_url):
        body = get_json(
            APIClient(api_base_url).post(
                "/login", json={"email": "eve.holt@reqres.in", "password": "cityslicka"}
            )
        )
        assert "token" in body and body["token"]

    def test_register_returns_id_and_token(self, api_base_url):
        body = get_json(
            APIClient(api_base_url).post(
                "/register", json={"email": "eve.holt@reqres.in", "password": "pistol"}
            )
        )
        assert "id" in body and "token" in body

    def test_login_missing_password_returns_400(self, api_base_url):
        assert_status(
            APIClient(api_base_url).post("/login", json={"email": "eve.holt@reqres.in"}),
            400,
        )

    def test_invalid_endpoint_returns_404(self, api_base_url):
        assert_status(APIClient(api_base_url).get("/nonexistent_endpoint_xyz"), 404)
