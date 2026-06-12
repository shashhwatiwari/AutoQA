"""
Cart + Checkout test suite — saucedemo.com

Positive E2E flow:
  login → add items → verify cart → checkout info → verify order summary
  → confirm order → assert confirmation screen

Additional coverage:
  - multi-item add
  - price math (subtotal + tax == total)
  - remove item from cart
  - cancel checkout returns to cart
  - sort by price before adding
"""
import pytest
from pages.inventory_page import InventoryPage
from pages.cart_page import CartPage
from pages.checkout_page import CheckoutPage


# -----------------------------------------------------------------------
# Positive end-to-end purchase flow
# -----------------------------------------------------------------------

@pytest.mark.ui
@pytest.mark.regression
class TestEndToEndCheckout:

    def test_single_item_full_checkout(self, authenticated_driver, base_url):
        """
        Happy path: add one item → cart → checkout → confirm.
        Assertions at every stage so failures pinpoint the broken step.
        """
        driver = authenticated_driver

        # 1. Inventory — add first item
        inventory = InventoryPage(driver, base_url)
        inventory.open()
        first_item_name = inventory.get_item_names()[0]
        first_item_price = inventory.get_item_prices()[0]
        inventory.add_item_to_cart(0)

        assert inventory.get_cart_count() == 1, "Badge should show 1 after add"

        # 2. Cart — verify item landed
        inventory.go_to_cart()
        cart = CartPage(driver, base_url)

        assert cart.get_item_count() == 1
        assert cart.is_item_in_cart(first_item_name)
        assert cart.get_item_prices()[0] == pytest.approx(first_item_price)

        # 3. Checkout step one — fill customer info
        cart.proceed_to_checkout()
        checkout = CheckoutPage(driver, base_url)
        checkout.fill_info("Jane", "Doe", "10001")

        assert "checkout-step-two" in driver.current_url, "Should advance to overview"

        # 4. Checkout step two — verify price summary
        assert checkout.get_overview_item_names() == [first_item_name]
        subtotal = checkout.get_subtotal()
        tax = checkout.get_tax()
        total = checkout.get_total()

        assert subtotal == pytest.approx(first_item_price, rel=1e-2)
        assert total == pytest.approx(subtotal + tax, rel=1e-2)

        # 5. Confirm order
        checkout.finish()

        assert "checkout-complete" in driver.current_url
        assert checkout.is_order_complete()
        assert "Thank you" in checkout.get_complete_header_text()
        assert checkout.get_complete_body_text() != ""

    def test_multi_item_full_checkout(self, authenticated_driver, base_url):
        """Add two specific items, verify both appear in overview and math is correct."""
        driver = authenticated_driver

        inventory = InventoryPage(driver, base_url)
        inventory.open()

        # Add the cheapest two items to keep math easy
        inventory.sort_by("lohi")
        names = inventory.get_item_names()
        prices = inventory.get_item_prices()

        item_a, price_a = names[0], prices[0]
        item_b, price_b = names[1], prices[1]

        inventory.add_item_to_cart(0)
        inventory.add_item_to_cart(1)
        assert inventory.get_cart_count() == 2

        inventory.go_to_cart()
        cart = CartPage(driver, base_url)
        assert cart.get_item_count() == 2
        assert cart.is_item_in_cart(item_a)
        assert cart.is_item_in_cart(item_b)

        cart.proceed_to_checkout()
        checkout = CheckoutPage(driver, base_url)
        checkout.fill_info("John", "Smith", "90210")

        subtotal = checkout.get_subtotal()
        tax = checkout.get_tax()
        total = checkout.get_total()

        assert subtotal == pytest.approx(price_a + price_b, rel=1e-2)
        assert total == pytest.approx(subtotal + tax, rel=1e-2)

        checkout.finish()
        assert checkout.is_order_complete()

    def test_back_home_after_order_returns_to_inventory(self, authenticated_driver, base_url):
        driver = authenticated_driver

        inventory = InventoryPage(driver, base_url)
        inventory.open()
        inventory.add_item_to_cart(0)
        inventory.go_to_cart()

        cart = CartPage(driver, base_url)
        cart.proceed_to_checkout()

        checkout = CheckoutPage(driver, base_url)
        checkout.fill_info("Jane", "Doe", "10001")
        checkout.finish()

        assert checkout.is_order_complete()
        checkout.go_back_home()

        assert "inventory" in driver.current_url


# -----------------------------------------------------------------------
# Cart behaviour
# -----------------------------------------------------------------------

@pytest.mark.ui
@pytest.mark.regression
class TestCartBehaviour:

    def test_add_item_increments_badge(self, authenticated_driver, base_url):
        inventory = InventoryPage(authenticated_driver, base_url)
        inventory.open()
        assert inventory.get_cart_count() == 0
        inventory.add_item_to_cart(0)
        assert inventory.get_cart_count() == 1

    def test_adding_six_items_badge_shows_six(self, authenticated_driver, base_url):
        inventory = InventoryPage(authenticated_driver, base_url)
        inventory.open()
        inventory.add_all_items_to_cart()
        assert inventory.get_cart_count() == 6

    def test_remove_item_from_cart_empties_cart(self, authenticated_driver, base_url):
        inventory = InventoryPage(authenticated_driver, base_url)
        inventory.open()
        inventory.add_item_to_cart(0)
        inventory.go_to_cart()

        cart = CartPage(authenticated_driver, base_url)
        cart.remove_item(0)
        assert cart.get_item_count() == 0

    def test_continue_shopping_returns_to_inventory(self, authenticated_driver, base_url):
        inventory = InventoryPage(authenticated_driver, base_url)
        inventory.open()
        inventory.add_item_to_cart(0)
        inventory.go_to_cart()

        cart = CartPage(authenticated_driver, base_url)
        cart.continue_shopping()
        assert "inventory" in authenticated_driver.current_url

    def test_cart_shows_correct_item_name_after_add(self, authenticated_driver, base_url):
        inventory = InventoryPage(authenticated_driver, base_url)
        inventory.open()
        names = inventory.get_item_names()
        inventory.add_item_to_cart(2)
        inventory.go_to_cart()

        cart = CartPage(authenticated_driver, base_url)
        assert cart.is_item_in_cart(names[2])

    def test_item_quantities_are_one_each(self, authenticated_driver, base_url):
        inventory = InventoryPage(authenticated_driver, base_url)
        inventory.open()
        inventory.add_item_to_cart(0)
        inventory.add_item_to_cart(1)
        inventory.go_to_cart()

        cart = CartPage(authenticated_driver, base_url)
        for qty in cart.get_item_quantities():
            assert qty == 1


# -----------------------------------------------------------------------
# Checkout validation (negative paths within positive flow)
# -----------------------------------------------------------------------

@pytest.mark.ui
@pytest.mark.regression
class TestCheckoutValidation:

    def _reach_checkout_step_one(self, driver, base_url):
        inventory = InventoryPage(driver, base_url)
        inventory.open()
        inventory.add_item_to_cart(0)
        inventory.go_to_cart()
        CartPage(driver, base_url).proceed_to_checkout()
        return CheckoutPage(driver, base_url)

    def test_missing_first_name_shows_error(self, authenticated_driver, base_url):
        checkout = self._reach_checkout_step_one(authenticated_driver, base_url)
        checkout.fill_info("", "Doe", "10001")

        assert checkout.is_error_displayed()
        assert "First Name is required" in checkout.get_error_message()

    def test_missing_last_name_shows_error(self, authenticated_driver, base_url):
        checkout = self._reach_checkout_step_one(authenticated_driver, base_url)
        checkout.fill_info("Jane", "", "10001")

        assert checkout.is_error_displayed()
        assert "Last Name is required" in checkout.get_error_message()

    def test_missing_postal_code_shows_error(self, authenticated_driver, base_url):
        checkout = self._reach_checkout_step_one(authenticated_driver, base_url)
        checkout.fill_info("Jane", "Doe", "")

        assert checkout.is_error_displayed()
        assert "Postal Code is required" in checkout.get_error_message()

    def test_cancel_on_step_one_returns_to_cart(self, authenticated_driver, base_url):
        checkout = self._reach_checkout_step_one(authenticated_driver, base_url)
        checkout.cancel_step_one()

        assert "cart" in authenticated_driver.current_url

    def test_cancel_on_step_two_returns_to_inventory(self, authenticated_driver, base_url):
        checkout = self._reach_checkout_step_one(authenticated_driver, base_url)
        checkout.fill_info("Jane", "Doe", "10001")
        checkout.cancel_overview()

        assert "inventory" in authenticated_driver.current_url
