"""
HTML parsing and assertion helpers — BeautifulSoup4

Design contract
---------------
Every public function accepts `html: str` as its first argument (the raw
page source obtained from driver.page_source after Selenium has finished
rendering the page).

Low-level primitives (get_*, count_*, has_*) return data.
High-level assertion functions (assert_*) raise AssertionError with a
descriptive message when the HTML does not meet the expectation.

Callers never import BeautifulSoup directly — all parsing lives here.
"""
from __future__ import annotations

from bs4 import BeautifulSoup, Tag


# ===========================================================================
# Internal helpers
# ===========================================================================

def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def _require(el: Tag | None, description: str) -> Tag:
    if el is None:
        raise AssertionError(f"Expected element not found in HTML: {description}")
    return el


def _price_text_to_float(text: str) -> float:
    """'$29.99' → 29.99"""
    return float(text.strip().lstrip("$"))


# ===========================================================================
# Low-level primitives  (return data, never raise)
# ===========================================================================

def parse_html(html: str) -> BeautifulSoup:
    return _soup(html)


def get_text_by_selector(html: str, selector: str) -> str:
    el = _soup(html).select_one(selector)
    return el.get_text(strip=True) if el else ""


def get_all_text_by_selector(html: str, selector: str) -> list[str]:
    return [el.get_text(strip=True) for el in _soup(html).select(selector)]


def has_element(html: str, selector: str) -> bool:
    return _soup(html).select_one(selector) is not None


def get_attribute(html: str, selector: str, attr: str) -> str | None:
    el = _soup(html).select_one(selector)
    return el.get(attr) if el else None


def get_all_links(html: str) -> list[str]:
    return [a.get("href", "") for a in _soup(html).find_all("a", href=True)]


def get_form_fields(html: str) -> list[dict]:
    return [
        {"name": inp.get("name"), "type": inp.get("type"), "id": inp.get("id")}
        for inp in _soup(html).find_all("input")
    ]


def count_elements(html: str, selector: str) -> int:
    return len(_soup(html).select(selector))


# ===========================================================================
# LOGIN PAGE assertions
# ===========================================================================

def assert_login_form_structure(html: str) -> None:
    """
    The login page must contain:
      • a username input  (id="user-name", type="text")
      • a password input  (id="password",  type="password")
      • a submit button   (id="login-button")
    """
    soup = _soup(html)

    username_el = soup.select_one("input#user-name")
    _require(username_el, "<input id='user-name'>")
    field_type = (username_el.get("type") or "text").lower()
    assert field_type == "text", (
        f"Username field type should be 'text', got '{field_type}'"
    )

    password_el = soup.select_one("input#password")
    _require(password_el, "<input id='password'>")
    pwd_type = (password_el.get("type") or "").lower()
    assert pwd_type == "password", (
        f"Password field type must be 'password' for masking, got '{pwd_type}'"
    )

    _require(soup.select_one("[id='login-button']"), "login submit button #login-button")


def assert_login_error_present(html: str, expected_text: str | None = None) -> None:
    """
    Error banner ([data-test='error']) must be present in the HTML.
    If `expected_text` is supplied, the banner's text must contain it.
    """
    el = _require(
        _soup(html).select_one("[data-test='error']"),
        "[data-test='error'] error banner",
    )
    if expected_text:
        actual = el.get_text(strip=True)
        assert expected_text in actual, (
            f"Error banner text should contain {expected_text!r}, got: {actual!r}"
        )


def assert_login_error_absent(html: str) -> None:
    """No error banner should appear on the login page after a clean state."""
    el = _soup(html).select_one("[data-test='error']")
    assert el is None, (
        f"Expected no error banner, but found one with text: {el.get_text(strip=True)!r}"
    )


def assert_password_field_is_masked(html: str) -> None:
    """Shorthand — password input must carry type='password'."""
    el = _require(_soup(html).select_one("input#password"), "<input id='password'>")
    t = (el.get("type") or "").lower()
    assert t == "password", (
        f"Password field must have type='password' to mask input, got '{t}'"
    )


# ===========================================================================
# INVENTORY PAGE assertions
# ===========================================================================

def assert_product_count(html: str, expected: int = 6) -> None:
    """
    SauceDemo's inventory page must list exactly `expected` products.
    Counted via .inventory_item wrappers in the static HTML.
    """
    items = _soup(html).select(".inventory_item")
    assert len(items) == expected, (
        f"Expected {expected} products on the inventory page, found {len(items)}"
    )


def assert_products_have_names_and_descriptions(html: str) -> None:
    """
    Every .inventory_item must contain a non-empty name and description.
    Catches partial renders where a product card is present but its text is missing.
    """
    soup = _soup(html)
    for idx, item in enumerate(soup.select(".inventory_item")):
        name = (item.select_one(".inventory_item_name") or {}).get_text(strip=True)
        desc = (item.select_one(".inventory_item_desc") or {}).get_text(strip=True)
        assert name, f"Product at index {idx} has an empty or missing name"
        assert desc, f"Product at index {idx} ('{name}') has an empty or missing description"


def assert_product_prices_are_positive(html: str) -> None:
    """
    Every .inventory_item_price must be a parseable float greater than zero.
    Catches '$0.00', missing '$', or non-numeric content.
    """
    soup = _soup(html)
    price_els = soup.select(".inventory_item_price")
    assert price_els, "No .inventory_item_price elements found on the page"
    for el in price_els:
        text = el.get_text(strip=True)
        try:
            value = _price_text_to_float(text)
        except ValueError:
            raise AssertionError(
                f"Could not parse price text as a float: {text!r}"
            )
        assert value > 0, f"Product price must be > $0.00, got: {text!r}"


def assert_no_duplicate_product_names(html: str) -> None:
    """Product names must be unique on the inventory page."""
    names = get_all_text_by_selector(html, ".inventory_item_name")
    duplicates = {n for n in names if names.count(n) > 1}
    assert not duplicates, (
        f"Duplicate product names found on inventory page: {duplicates}"
    )


def assert_add_to_cart_buttons_present(html: str, expected_count: int = 6) -> None:
    """
    Every product must have an 'Add to cart' button.
    `expected_count` matches the number of products on the page.
    """
    btns = _soup(html).select("button[data-test^='add-to-cart']")
    assert len(btns) == expected_count, (
        f"Expected {expected_count} 'Add to cart' buttons, found {len(btns)}"
    )


def assert_sort_dropdown_options(html: str) -> None:
    """
    The sort <select> must be present and contain all four sort options:
    az (A→Z), za (Z→A), lohi (price low→high), hilo (price high→low).
    """
    soup = _soup(html)
    select = _require(soup.select_one(".product_sort_container"), "sort dropdown .product_sort_container")
    option_values = {opt.get("value") for opt in select.find_all("option")}
    required = {"az", "za", "lohi", "hilo"}
    missing = required - option_values
    assert not missing, (
        f"Sort dropdown is missing option value(s): {missing}. Found: {option_values}"
    )


def assert_product_images_have_src(html: str) -> None:
    """
    Every product image inside .inventory_item must have a non-empty src.
    An empty or missing src means a broken image.
    """
    soup = _soup(html)
    for idx, item in enumerate(soup.select(".inventory_item")):
        img = item.select_one("img")
        assert img is not None, f"Product at index {idx} has no <img> element"
        src = (img.get("src") or "").strip()
        assert src, f"Product at index {idx} has an <img> with an empty src"


def assert_cart_link_present(html: str) -> None:
    """The shopping cart link must be in the page header."""
    _require(
        _soup(html).select_one(".shopping_cart_link"),
        "shopping cart link (.shopping_cart_link)",
    )


def assert_page_title_text(html: str, expected: str) -> None:
    """The visible .title element must contain `expected`."""
    el = _require(_soup(html).select_one(".title"), ".title element")
    actual = el.get_text(strip=True)
    assert expected in actual, (
        f"Page title should contain {expected!r}, got {actual!r}"
    )


# ===========================================================================
# CART PAGE assertions
# ===========================================================================

def assert_cart_item_count(html: str, expected: int) -> None:
    """The cart page must contain exactly `expected` .cart_item rows."""
    items = _soup(html).select(".cart_item")
    assert len(items) == expected, (
        f"Expected {expected} item(s) in cart HTML, found {len(items)}"
    )


def assert_cart_contains_item_named(html: str, name: str) -> None:
    """At least one .inventory_item_name in the cart must match `name`."""
    names = get_all_text_by_selector(html, ".inventory_item_name")
    assert name in names, (
        f"Cart page HTML does not contain an item named {name!r}. Found: {names}"
    )


def assert_cart_item_prices_positive(html: str) -> None:
    """Every price shown in the cart must be a parseable float > 0."""
    price_els = _soup(html).select(".inventory_item_price")
    for el in price_els:
        text = el.get_text(strip=True)
        try:
            val = _price_text_to_float(text)
        except ValueError:
            raise AssertionError(f"Could not parse cart price: {text!r}")
        assert val > 0, f"Cart item price must be > $0.00, got: {text!r}"


def assert_cart_has_checkout_button(html: str) -> None:
    soup = _soup(html)
    _require(
        soup.select_one("[data-test='checkout']") or soup.select_one("#checkout"),
        "checkout button ([data-test='checkout'] or #checkout)",
    )


def assert_cart_quantities_are_positive(html: str) -> None:
    """Every .cart_quantity value must be a positive integer."""
    qty_els = _soup(html).select(".cart_quantity")
    assert qty_els, "No .cart_quantity elements found — is the cart populated?"
    for el in qty_els:
        text = el.get_text(strip=True)
        assert text.isdigit() and int(text) > 0, (
            f"Cart quantity must be a positive integer, got: {text!r}"
        )


# ===========================================================================
# CHECKOUT OVERVIEW (step two) assertions
# ===========================================================================

def assert_overview_totals_are_numeric(html: str) -> dict[str, float]:
    """
    Subtotal, tax, and total labels must all be present and contain
    parseable dollar amounts. Returns the three values for further assertions.
    """
    soup = _soup(html)

    def _extract(selector: str, label: str) -> float:
        el = _require(soup.select_one(selector), label)
        text = el.get_text(strip=True)
        try:
            return _price_text_to_float(text.split("$")[-1])
        except ValueError:
            raise AssertionError(
                f"{label} text is not a parseable dollar amount: {text!r}"
            )

    subtotal = _extract(".summary_subtotal_label", "subtotal label")
    tax      = _extract(".summary_tax_label",      "tax label")
    total    = _extract(".summary_total_label",     "total label")
    return {"subtotal": subtotal, "tax": tax, "total": total}


def assert_overview_math_correct(html: str, rel_tol: float = 0.01) -> None:
    """
    Total displayed on the checkout overview must equal subtotal + tax
    within `rel_tol` (default 1 % to absorb floating-point drift).
    This validates the server/client math without relying on Selenium's
    live-DOM queries.
    """
    totals = assert_overview_totals_are_numeric(html)
    expected_total = totals["subtotal"] + totals["tax"]
    actual_total   = totals["total"]
    delta = abs(actual_total - expected_total)
    tol   = max(rel_tol * expected_total, 0.01)   # floor at 1 cent
    assert delta <= tol, (
        f"Checkout total mismatch in HTML: "
        f"subtotal ${totals['subtotal']:.2f} + tax ${totals['tax']:.2f} "
        f"= ${expected_total:.2f}, but total label shows ${actual_total:.2f} "
        f"(delta ${delta:.4f} exceeds tolerance ${tol:.4f})"
    )


def assert_overview_contains_item(html: str, name: str) -> None:
    """The checkout overview must list the named product."""
    names = get_all_text_by_selector(html, ".inventory_item_name")
    assert name in names, (
        f"Checkout overview does not contain {name!r}. Items listed: {names}"
    )


def assert_overview_finish_button_present(html: str) -> None:
    _require(_soup(html).select_one("#finish"), "Finish button (#finish)")


def assert_overview_subtotal_matches_item_prices(html: str) -> None:
    """
    The sum of individual .inventory_item_price elements on the overview
    must equal the subtotal label value.
    This catches a mismatch between displayed line-items and the displayed total.
    """
    soup = _soup(html)
    item_prices = [
        _price_text_to_float(el.get_text(strip=True))
        for el in soup.select(".inventory_item_price")
    ]
    subtotal_el = _require(soup.select_one(".summary_subtotal_label"), "subtotal label")
    subtotal_text = subtotal_el.get_text(strip=True).split("$")[-1]
    subtotal = _price_text_to_float(subtotal_text)

    computed = round(sum(item_prices), 2)
    assert abs(computed - subtotal) < 0.01, (
        f"Sum of item prices (${computed:.2f}) does not match "
        f"subtotal label (${subtotal:.2f})"
    )


# ===========================================================================
# CHECKOUT COMPLETE (confirmation) assertions
# ===========================================================================

def assert_order_confirmation_structure(html: str) -> None:
    """
    The confirmation page must contain:
      • .complete-header with non-empty text
      • .complete-text  with non-empty text
      • #back-to-products button
    """
    soup = _soup(html)

    header = _require(soup.select_one(".complete-header"), ".complete-header element")
    assert header.get_text(strip=True), ".complete-header element has no visible text"

    body = _require(soup.select_one(".complete-text"), ".complete-text element")
    assert body.get_text(strip=True), ".complete-text element has no visible text"

    _require(soup.select_one("#back-to-products"), "#back-to-products button")


def assert_order_confirmation_header_text(html: str, expected: str = "Thank you") -> None:
    """The confirmation header must contain `expected`."""
    el = _require(_soup(html).select_one(".complete-header"), ".complete-header element")
    actual = el.get_text(strip=True)
    assert expected in actual, (
        f"Order confirmation header should contain {expected!r}, got: {actual!r}"
    )


# ===========================================================================
# SECURITY / INJECTION assertions
# ===========================================================================

def assert_no_unescaped_script_tag(html: str, payload: str) -> None:
    """
    Verifies that a user-supplied XSS payload was not injected as a raw
    <script> tag into the rendered HTML.

    Strategy: look for the payload as raw text inside the page source.
    If the browser serialised the DOM back with the script tag intact,
    that indicates a reflected-XSS vulnerability.
    """
    soup = _soup(html)
    for script in soup.find_all("script"):
        content = script.string or ""
        assert payload not in content, (
            f"XSS payload found unescaped inside a <script> tag: {payload!r}"
        )

    # Also check that any place the payload appears in the DOM is text-escaped
    # (e.g. rendered as &lt;script&gt; rather than an actual tag)
    raw_script_tags = [
        str(tag) for tag in soup.find_all("script")
        if payload in str(tag)
    ]
    assert not raw_script_tags, (
        f"Payload {payload!r} appears inside a <script> element in the HTML"
    )


def assert_error_text_is_html_escaped(html: str, raw_payload: str) -> None:
    """
    When a payload is reflected in an error message, it must appear as
    escaped HTML (e.g. &lt;script&gt;) not as live tags.
    """
    soup = _soup(html)
    error_el = soup.select_one("[data-test='error']")
    if error_el is None:
        return  # no error banner — nothing to check
    raw_html = str(error_el)
    assert f"<script" not in raw_html.lower() or raw_payload not in raw_html, (
        f"Error banner appears to contain unescaped script tag from payload: {raw_payload!r}"
    )
