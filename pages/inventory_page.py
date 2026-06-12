from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from pages.base_page import BasePage


class InventoryPage(BasePage):
    PATH = "/inventory.html"

    _TITLE = (By.CLASS_NAME, "title")
    _ITEMS = (By.CLASS_NAME, "inventory_item")
    _ITEM_NAMES = (By.CLASS_NAME, "inventory_item_name")
    _ITEM_PRICES = (By.CLASS_NAME, "inventory_item_price")
    _ITEM_DESCS = (By.CLASS_NAME, "inventory_item_desc")
    _ADD_TO_CART_BTNS = (By.CSS_SELECTOR, "button[data-test^='add-to-cart']")
    _REMOVE_BTNS = (By.CSS_SELECTOR, "button[data-test^='remove']")
    _CART_BADGE = (By.CLASS_NAME, "shopping_cart_badge")
    _CART_ICON = (By.CLASS_NAME, "shopping_cart_link")
    _SORT_DROPDOWN = (By.CLASS_NAME, "product_sort_container")
    _BURGER_MENU = (By.ID, "react-burger-menu-btn")
    _LOGOUT_LINK = (By.ID, "logout_sidebar_link")

    def open(self):
        super().open(self.PATH)
        self.wait_for_visible(self._TITLE)

    # ------------------------------------------------------------------
    # Item queries
    # ------------------------------------------------------------------

    def get_item_names(self) -> list[str]:
        self.wait_for_visible(self._ITEMS)
        return [el.text for el in self.driver.find_elements(*self._ITEM_NAMES)]

    def get_item_prices(self) -> list[float]:
        return [
            float(el.text.replace("$", ""))
            for el in self.driver.find_elements(*self._ITEM_PRICES)
        ]

    def get_item_count(self) -> int:
        return len(self.driver.find_elements(*self._ITEMS))

    def get_item_price_by_name(self, name: str) -> float:
        names = self.get_item_names()
        prices = self.get_item_prices()
        idx = names.index(name)
        return prices[idx]

    # ------------------------------------------------------------------
    # Cart actions
    # ------------------------------------------------------------------

    def add_item_to_cart(self, index: int = 0):
        """Click the Add-to-cart button for the item at ``index``.

        Locates the button within the item's own container so the index is
        stable even when earlier items are already in the cart (their buttons
        have turned into Remove buttons, shrinking the global add-to-cart
        list). Waits for the matching Remove button to appear before returning,
        which confirms the React cart state has been committed and makes
        subsequent badge/count assertions reliable.
        """
        self.wait_for_element_count(self._ITEMS, index + 1)
        item = self.driver.find_elements(*self._ITEMS)[index]
        btn = item.find_element(By.CSS_SELECTOR, "button[data-test^='add-to-cart']")
        data_test = btn.get_attribute("data-test")
        btn.click()
        remove_attr = data_test.replace("add-to-cart-", "remove-", 1)
        self.wait_for_visible((By.CSS_SELECTOR, f"button[data-test='{remove_attr}']"))

    def add_item_by_name(self, name: str):
        names = self.get_item_names()
        idx = names.index(name)
        self.add_item_to_cart(idx)

    def add_all_items_to_cart(self):
        self.wait_for_element_count(self._ITEMS, 1)
        for item in self.driver.find_elements(*self._ITEMS):
            try:
                btn = item.find_element(By.CSS_SELECTOR, "button[data-test^='add-to-cart']")
                btn.click()
            except Exception:
                pass  # item already in cart

    def get_cart_count(self) -> int:
        if not self.is_visible(self._CART_BADGE, timeout=2):
            return 0
        return int(self.get_text(self._CART_BADGE))

    def go_to_cart(self):
        self.click(self._CART_ICON)

    # ------------------------------------------------------------------
    # Sort
    # ------------------------------------------------------------------

    def sort_by(self, option_value: str):
        """option_value: az | za | lohi | hilo"""
        select = Select(self.driver.find_element(*self._SORT_DROPDOWN))
        select.select_by_value(option_value)

    def get_current_sort(self) -> str:
        select = Select(self.driver.find_element(*self._SORT_DROPDOWN))
        return select.first_selected_option.get_attribute("value")

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def logout(self):
        self.click(self._BURGER_MENU)
        self.click(self._LOGOUT_LINK)
