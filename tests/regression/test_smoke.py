import pytest
from pages.login_page import LoginPage
from pages.inventory_page import InventoryPage
from utils.api_client import APIClient, assert_status


@pytest.mark.smoke
@pytest.mark.regression
class TestSmoke:

    def test_login_page_loads(self, driver, base_url):
        login = LoginPage(driver, base_url)
        login.open()
        assert login.is_visible(login._LOGIN_BTN)

    def test_valid_login_reaches_inventory(self, driver, base_url):
        login = LoginPage(driver, base_url)
        login.open()
        login.login("standard_user", "secret_sauce")

        inventory = InventoryPage(driver, base_url)
        inventory.wait_for_visible(inventory._TITLE)
        assert "inventory" in driver.current_url

    def test_inventory_page_has_items(self, authenticated_driver, base_url):
        inventory = InventoryPage(authenticated_driver, base_url)
        inventory.open()
        names = inventory.get_item_names()
        assert len(names) > 0

    def test_api_users_endpoint_alive(self, api_base_url):
        client = APIClient(api_base_url)
        resp = client.get("/users")
        assert_status(resp, 200)

    def test_api_login_endpoint_alive(self, api_base_url):
        client = APIClient(api_base_url)
        resp = client.post(
            "/login",
            json={"email": "eve.holt@reqres.in", "password": "cityslicka"},
        )
        assert_status(resp, 200)
