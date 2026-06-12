from selenium.webdriver.common.by import By
from pages.base_page import BasePage


class CartPage(BasePage):
    PATH = "/cart.html"

    _CART_ITEMS = (By.CLASS_NAME, "cart_item")
    _ITEM_NAMES = (By.CLASS_NAME, "inventory_item_name")
    _ITEM_PRICES = (By.CLASS_NAME, "inventory_item_price")
    _ITEM_QUANTITIES = (By.CLASS_NAME, "cart_quantity")
    _CHECKOUT_BTN = (By.ID, "checkout")
    _CONTINUE_SHOPPING_BTN = (By.ID, "continue-shopping")
    _REMOVE_BTNS = (By.CSS_SELECTOR, "button[data-test^='remove']")

    def open(self):
        super().open(self.PATH)

    def get_item_names(self) -> list[str]:
        return [el.text for el in self.driver.find_elements(*self._ITEM_NAMES)]

    def get_item_prices(self) -> list[float]:
        return [
            float(el.text.replace("$", ""))
            for el in self.driver.find_elements(*self._ITEM_PRICES)
        ]

    def get_item_quantities(self) -> list[int]:
        return [
            int(el.text)
            for el in self.driver.find_elements(*self._ITEM_QUANTITIES)
        ]

    def get_item_count(self) -> int:
        return len(self.driver.find_elements(*self._CART_ITEMS))

    def is_item_in_cart(self, name: str) -> bool:
        return name in self.get_item_names()

    def remove_item(self, index: int = 0):
        self.driver.find_elements(*self._REMOVE_BTNS)[index].click()

    def remove_item_by_name(self, name: str):
        names = self.get_item_names()
        idx = names.index(name)
        self.remove_item(idx)

    def proceed_to_checkout(self):
        self.click(self._CHECKOUT_BTN)

    def continue_shopping(self):
        self.click(self._CONTINUE_SHOPPING_BTN)

    def is_empty(self) -> bool:
        return self.get_item_count() == 0
