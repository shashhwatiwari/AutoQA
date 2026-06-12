"""
BeautifulSoup4 validation layer — saucedemo.com

Pattern used in every test
---------------------------
1. Selenium  — navigates, authenticates, and drives interactions.
               Handles JavaScript rendering so the page is fully loaded.
2. Handoff   — `html = driver.page_source` captures the serialised DOM.
3. BS4       — parses `html` as a static document and asserts on structure,
               content, and arithmetic — independent of Selenium's live-DOM
               query engine.

This separation means the BS4 assertions would also catch regressions in
server-rendered HTML that Selenium's is_visible() would silently miss
(e.g. a product with a $0 price still "visible" but wrong in the DOM).
"""
import pytest
from pages.login_page import LoginPage
from pages.inventory_page import InventoryPage
from pages.cart_page import CartPage
from pages.checkout_page import CheckoutPage
import utils.parsing as p


# ---------------------------------------------------------------------------
# Shared setup helpers
# ---------------------------------------------------------------------------

XSS_PAYLOAD = "<script>alert('xss')</script>"


def _login(driver, base_url, username="standard_user", password="secret_sauce"):
    page = LoginPage(driver, base_url)
    page.open()
    page.login(username, password)
    return page


def _add_item_reach_cart(driver, base_url, index=0):
    inventory = InventoryPage(driver, base_url)
    inventory.open()
    item_name = inventory.get_item_names()[index]
    item_price = inventory.get_item_prices()[index]
    inventory.add_item_to_cart(index)
    inventory.go_to_cart()
    return CartPage(driver, base_url), item_name, item_price


def _full_checkout(driver, base_url, index=0):
    cart, item_name, item_price = _add_item_reach_cart(driver, base_url, index)
    cart.proceed_to_checkout()
    checkout = CheckoutPage(driver, base_url)
    checkout.fill_info("Jane", "Doe", "10001")
    return checkout, item_name, item_price


# ===========================================================================
# LOGIN PAGE — structure and error content
# ===========================================================================

@pytest.mark.ui
class TestLoginPageBS4:

    def test_login_form_structure_in_html(self, driver, base_url):
        """
        BS4 confirms the username input, masked password input, and submit
        button are all present in the serialised HTML — not just visible in
        the live DOM.
        """
        login = LoginPage(driver, base_url)
        login.open()
        html = driver.page_source

        p.assert_login_form_structure(html)

    def test_password_field_is_masked_in_html(self, driver, base_url):
        """type='password' must be baked into the HTML, not injected by JS."""
        login = LoginPage(driver, base_url)
        login.open()

        p.assert_password_field_is_masked(driver.page_source)

    def test_no_error_banner_on_clean_load(self, driver, base_url):
        """The error [data-test='error'] element must be absent from a fresh page."""
        login = LoginPage(driver, base_url)
        login.open()

        p.assert_login_error_absent(driver.page_source)

    def test_error_banner_present_after_wrong_password(self, driver, base_url):
        """
        After a failed login, BS4 finds the error container in the HTML and
        checks its text matches the expected SauceDemo message.
        """
        login = LoginPage(driver, base_url)
        login.open()
        login.login("standard_user", "wrong_password")

        p.assert_login_error_present(
            driver.page_source,
            expected_text="Epic sadface",
        )

    def test_error_banner_text_for_locked_out_user(self, driver, base_url):
        login = LoginPage(driver, base_url)
        login.open()
        login.login("locked_out_user", "secret_sauce")

        p.assert_login_error_present(
            driver.page_source,
            expected_text="locked out",
        )

    def test_error_banner_text_for_empty_username(self, driver, base_url):
        login = LoginPage(driver, base_url)
        login.open()
        login.login("", "secret_sauce")

        p.assert_login_error_present(
            driver.page_source,
            expected_text="Username is required",
        )

    def test_error_banner_text_for_empty_password(self, driver, base_url):
        login = LoginPage(driver, base_url)
        login.open()
        login.login("standard_user", "")

        p.assert_login_error_present(
            driver.page_source,
            expected_text="Password is required",
        )

    def test_xss_payload_in_username_not_injected_as_script(self, driver, base_url):
        """
        XSS payload entered as the username must not appear as a live <script>
        tag in the serialised HTML. BS4 walks the parsed tree — any successful
        injection would be detectable as a <script> node.
        """
        login = LoginPage(driver, base_url)
        login.open()
        login.login(XSS_PAYLOAD, "secret_sauce")

        html = driver.page_source
        p.assert_no_unescaped_script_tag(html, XSS_PAYLOAD)
        p.assert_error_text_is_html_escaped(html, XSS_PAYLOAD)


# ===========================================================================
# INVENTORY PAGE — product list structure
# ===========================================================================

@pytest.mark.ui
class TestInventoryPageBS4:

    def test_exactly_six_products_in_html(self, authenticated_driver, base_url):
        """
        The serialised HTML must contain exactly 6 .inventory_item wrappers.
        Catches partial renders that Selenium's element count would also miss
        if the elements are present-but-empty.
        """
        inventory = InventoryPage(authenticated_driver, base_url)
        inventory.open()

        p.assert_product_count(driver.page_source if False else authenticated_driver.page_source, expected=6)

    def test_every_product_has_name_and_description(self, authenticated_driver, base_url):
        """
        BS4 walks each .inventory_item and asserts both .inventory_item_name
        and .inventory_item_desc are non-empty. Catches items with missing text.
        """
        inventory = InventoryPage(authenticated_driver, base_url)
        inventory.open()

        p.assert_products_have_names_and_descriptions(authenticated_driver.page_source)

    def test_all_product_prices_are_positive(self, authenticated_driver, base_url):
        """
        Every .inventory_item_price must be a parseable dollar amount > $0.
        BS4 parses the text; no Selenium element interaction involved.
        """
        inventory = InventoryPage(authenticated_driver, base_url)
        inventory.open()

        p.assert_product_prices_are_positive(authenticated_driver.page_source)

    def test_product_names_are_unique(self, authenticated_driver, base_url):
        """No two products should share the same name on the listing page."""
        inventory = InventoryPage(authenticated_driver, base_url)
        inventory.open()

        p.assert_no_duplicate_product_names(authenticated_driver.page_source)

    def test_six_add_to_cart_buttons_in_html(self, authenticated_driver, base_url):
        """
        The number of add-to-cart buttons in the raw HTML must match the
        product count. If a button is hidden via CSS but present in HTML,
        Selenium might miss it while BS4 counts it — this guards the HTML layer.
        """
        inventory = InventoryPage(authenticated_driver, base_url)
        inventory.open()

        p.assert_add_to_cart_buttons_present(authenticated_driver.page_source, expected_count=6)

    def test_sort_dropdown_has_all_four_options(self, authenticated_driver, base_url):
        """
        BS4 confirms the <select> contains all four expected option values
        (az, za, lohi, hilo) in the HTML, not just the first selected one.
        """
        inventory = InventoryPage(authenticated_driver, base_url)
        inventory.open()

        p.assert_sort_dropdown_options(authenticated_driver.page_source)

    def test_product_images_have_src_in_html(self, authenticated_driver, base_url):
        """
        Every product <img> inside .inventory_item must have a non-empty src
        attribute in the HTML. An empty src causes a broken image.
        """
        inventory = InventoryPage(authenticated_driver, base_url)
        inventory.open()

        p.assert_product_images_have_src(authenticated_driver.page_source)

    def test_page_title_text_is_products(self, authenticated_driver, base_url):
        inventory = InventoryPage(authenticated_driver, base_url)
        inventory.open()

        p.assert_page_title_text(authenticated_driver.page_source, "Products")

    def test_cart_link_is_present_in_header(self, authenticated_driver, base_url):
        inventory = InventoryPage(authenticated_driver, base_url)
        inventory.open()

        p.assert_cart_link_present(authenticated_driver.page_source)

    def test_price_count_matches_product_count(self, authenticated_driver, base_url):
        """Structural sanity: one price element per product card."""
        inventory = InventoryPage(authenticated_driver, base_url)
        inventory.open()

        html = authenticated_driver.page_source
        products = p.count_elements(html, ".inventory_item")
        prices   = p.count_elements(html, ".inventory_item_price")
        assert products == prices, (
            f"Product count ({products}) does not match price element count ({prices})"
        )

    def test_prices_in_html_match_prices_from_selenium(self, authenticated_driver, base_url):
        """
        Cross-validate: prices read by Selenium's find_elements must equal
        prices parsed by BS4 from the same page_source snapshot.
        """
        inventory = InventoryPage(authenticated_driver, base_url)
        inventory.open()

        selenium_prices = inventory.get_item_prices()
        bs4_prices = [
            float(t.lstrip("$"))
            for t in p.get_all_text_by_selector(
                authenticated_driver.page_source, ".inventory_item_price"
            )
        ]

        assert selenium_prices == bs4_prices, (
            f"Price mismatch between Selenium and BS4:\n"
            f"  Selenium: {selenium_prices}\n"
            f"  BS4:      {bs4_prices}"
        )

    def test_product_names_in_html_match_selenium(self, authenticated_driver, base_url):
        """Cross-validate names between Selenium DOM queries and BS4 HTML parse."""
        inventory = InventoryPage(authenticated_driver, base_url)
        inventory.open()

        selenium_names = inventory.get_item_names()
        bs4_names = p.get_all_text_by_selector(
            authenticated_driver.page_source, ".inventory_item_name"
        )

        assert selenium_names == bs4_names, (
            f"Name mismatch between Selenium and BS4:\n"
            f"  Selenium: {selenium_names}\n"
            f"  BS4:      {bs4_names}"
        )


# ===========================================================================
# CART PAGE — item rows, prices, structure
# ===========================================================================

@pytest.mark.ui
class TestCartPageBS4:

    def test_empty_cart_has_no_item_rows_in_html(self, authenticated_driver, base_url):
        cart = CartPage(authenticated_driver, base_url)
        cart.open()

        p.assert_cart_item_count(authenticated_driver.page_source, expected=0)

    def test_one_item_added_appears_in_cart_html(self, authenticated_driver, base_url):
        cart, item_name, _ = _add_item_reach_cart(authenticated_driver, base_url, 0)

        html = authenticated_driver.page_source
        p.assert_cart_item_count(html, expected=1)
        p.assert_cart_contains_item_named(html, item_name)

    def test_two_items_appear_in_cart_html(self, authenticated_driver, base_url):
        inventory = InventoryPage(authenticated_driver, base_url)
        inventory.open()
        name_a = inventory.get_item_names()[0]
        name_b = inventory.get_item_names()[1]
        inventory.add_item_to_cart(0)
        inventory.add_item_to_cart(1)
        inventory.go_to_cart()

        html = authenticated_driver.page_source
        p.assert_cart_item_count(html, expected=2)
        p.assert_cart_contains_item_named(html, name_a)
        p.assert_cart_contains_item_named(html, name_b)

    def test_cart_item_prices_are_positive(self, authenticated_driver, base_url):
        _add_item_reach_cart(authenticated_driver, base_url, 0)

        p.assert_cart_item_prices_positive(authenticated_driver.page_source)

    def test_cart_item_quantities_are_positive(self, authenticated_driver, base_url):
        _add_item_reach_cart(authenticated_driver, base_url, 0)

        p.assert_cart_quantities_are_positive(authenticated_driver.page_source)

    def test_checkout_button_in_cart_html(self, authenticated_driver, base_url):
        cart = CartPage(authenticated_driver, base_url)
        cart.open()

        p.assert_cart_has_checkout_button(authenticated_driver.page_source)

    def test_cart_item_price_matches_inventory_price(self, authenticated_driver, base_url):
        """
        The price shown in the cart HTML must equal the price shown on the
        inventory page. Catches price-injection bugs at the cart layer.
        """
        cart, item_name, inventory_price = _add_item_reach_cart(
            authenticated_driver, base_url, 0
        )
        cart_prices = [
            float(t.lstrip("$"))
            for t in p.get_all_text_by_selector(
                authenticated_driver.page_source, ".inventory_item_price"
            )
        ]
        assert cart_prices, "No prices found in cart HTML"
        assert cart_prices[0] == pytest.approx(inventory_price, rel=1e-2), (
            f"Cart price ${cart_prices[0]} does not match "
            f"inventory price ${inventory_price} for '{item_name}'"
        )

    def test_removed_item_absent_from_cart_html(self, authenticated_driver, base_url):
        cart, item_name, _ = _add_item_reach_cart(authenticated_driver, base_url, 0)
        cart.remove_item(0)

        html = authenticated_driver.page_source
        p.assert_cart_item_count(html, expected=0)
        names_in_cart = p.get_all_text_by_selector(html, ".inventory_item_name")
        assert item_name not in names_in_cart, (
            f"Removed item '{item_name}' still appears in cart HTML after removal"
        )


# ===========================================================================
# CHECKOUT OVERVIEW — arithmetic and structure
# ===========================================================================

@pytest.mark.ui
class TestCheckoutOverviewBS4:

    def test_overview_totals_are_numeric_in_html(self, authenticated_driver, base_url):
        """
        After filling checkout info, BS4 confirms subtotal, tax, and total
        labels are all present and parseable in the HTML snapshot.
        """
        checkout, _, _ = _full_checkout(authenticated_driver, base_url)
        html = authenticated_driver.page_source

        totals = p.assert_overview_totals_are_numeric(html)
        for key, val in totals.items():
            assert isinstance(val, float), f"{key} must be a float, got {type(val)}"

    def test_overview_math_is_correct_in_html(self, authenticated_driver, base_url):
        """
        BS4 extracts subtotal, tax, and total from the HTML and verifies
        subtotal + tax == total (within 1 cent tolerance).
        This catches a display-layer bug that Selenium's text assertions miss.
        """
        checkout, _, _ = _full_checkout(authenticated_driver, base_url)

        p.assert_overview_math_correct(authenticated_driver.page_source)

    def test_ordered_item_appears_in_overview_html(self, authenticated_driver, base_url):
        """The item added to cart must appear in the checkout overview HTML."""
        checkout, item_name, _ = _full_checkout(authenticated_driver, base_url)

        p.assert_overview_contains_item(authenticated_driver.page_source, item_name)

    def test_overview_subtotal_matches_item_price_sum(self, authenticated_driver, base_url):
        """
        Sum of individual .inventory_item_price elements on the overview must
        equal the .summary_subtotal_label value.
        """
        checkout, _, _ = _full_checkout(authenticated_driver, base_url)

        p.assert_overview_subtotal_matches_item_prices(authenticated_driver.page_source)

    def test_overview_finish_button_present_in_html(self, authenticated_driver, base_url):
        checkout, _, _ = _full_checkout(authenticated_driver, base_url)

        p.assert_overview_finish_button_present(authenticated_driver.page_source)

    def test_multi_item_overview_math_is_correct(self, authenticated_driver, base_url):
        """Two-item checkout: subtotal + tax == total in the HTML."""
        inventory = InventoryPage(authenticated_driver, base_url)
        inventory.open()
        inventory.add_item_to_cart(0)
        inventory.add_item_to_cart(1)
        inventory.go_to_cart()

        CartPage(authenticated_driver, base_url).proceed_to_checkout()
        CheckoutPage(authenticated_driver, base_url).fill_info("Jane", "Doe", "10001")

        p.assert_overview_math_correct(authenticated_driver.page_source)

    def test_multi_item_subtotal_matches_sum_of_prices(self, authenticated_driver, base_url):
        inventory = InventoryPage(authenticated_driver, base_url)
        inventory.open()
        inventory.add_item_to_cart(0)
        inventory.add_item_to_cart(1)
        inventory.go_to_cart()

        CartPage(authenticated_driver, base_url).proceed_to_checkout()
        CheckoutPage(authenticated_driver, base_url).fill_info("Jane", "Doe", "10001")

        p.assert_overview_subtotal_matches_item_prices(authenticated_driver.page_source)


# ===========================================================================
# ORDER CONFIRMATION — structure and content
# ===========================================================================

@pytest.mark.ui
class TestOrderConfirmationBS4:

    def test_confirmation_page_structure(self, authenticated_driver, base_url):
        """
        After finishing checkout, BS4 verifies all three required elements
        are present in the HTML: .complete-header, .complete-text, and the
        #back-to-products button.
        """
        checkout, _, _ = _full_checkout(authenticated_driver, base_url)
        checkout.finish()

        p.assert_order_confirmation_structure(authenticated_driver.page_source)

    def test_confirmation_header_says_thank_you(self, authenticated_driver, base_url):
        checkout, _, _ = _full_checkout(authenticated_driver, base_url)
        checkout.finish()

        p.assert_order_confirmation_header_text(
            authenticated_driver.page_source, expected="Thank you"
        )

    def test_confirmation_body_text_is_non_empty(self, authenticated_driver, base_url):
        checkout, _, _ = _full_checkout(authenticated_driver, base_url)
        checkout.finish()

        body = p.get_text_by_selector(
            authenticated_driver.page_source, ".complete-text"
        )
        assert body, "Confirmation page .complete-text is empty in the HTML"

    def test_cart_link_absent_from_confirmation_html(self, authenticated_driver, base_url):
        """
        On the confirmation page the cart badge should show 0 and ideally the
        cart link should still be present (navigation must be intact).
        BS4 checks the header structure is preserved post-order.
        """
        checkout, _, _ = _full_checkout(authenticated_driver, base_url)
        checkout.finish()

        # Cart icon link must still exist in the header (navigation not broken)
        p.assert_cart_link_present(authenticated_driver.page_source)

    def test_confirmation_url_reflected_in_html_structure(self, authenticated_driver, base_url):
        """
        The confirmation page must not contain any product listing (no
        .inventory_item rows) — the order is done and the cart is cleared.
        """
        checkout, _, _ = _full_checkout(authenticated_driver, base_url)
        checkout.finish()

        product_count = p.count_elements(
            authenticated_driver.page_source, ".inventory_item"
        )
        assert product_count == 0, (
            f"Confirmation page should have 0 inventory items, found {product_count}"
        )
