from selenium.webdriver.common.by import By
from pages.base_page import BasePage


class CheckoutPage(BasePage):
    PATH_STEP_ONE = "/checkout-step-one.html"
    PATH_STEP_TWO = "/checkout-step-two.html"
    PATH_COMPLETE = "/checkout-complete.html"

    # Step one
    _FIRST_NAME = (By.ID, "first-name")
    _LAST_NAME = (By.ID, "last-name")
    _POSTAL_CODE = (By.ID, "postal-code")
    _CONTINUE_BTN = (By.ID, "continue")
    _CANCEL_BTN = (By.ID, "cancel")
    _ERROR_MSG = (By.CSS_SELECTOR, "[data-test='error']")

    # Step two
    _OVERVIEW_TITLE = (By.CLASS_NAME, "title")
    _ITEM_NAMES = (By.CLASS_NAME, "inventory_item_name")
    _ITEM_PRICES = (By.CLASS_NAME, "inventory_item_price")
    _SUBTOTAL = (By.CLASS_NAME, "summary_subtotal_label")
    _TAX = (By.CLASS_NAME, "summary_tax_label")
    _TOTAL = (By.CLASS_NAME, "summary_total_label")
    _FINISH_BTN = (By.ID, "finish")
    _CANCEL_OVERVIEW_BTN = (By.ID, "cancel")

    # Complete
    _COMPLETE_HEADER = (By.CLASS_NAME, "complete-header")
    _COMPLETE_TEXT = (By.CLASS_NAME, "complete-text")
    _BACK_HOME_BTN = (By.ID, "back-to-products")

    # ------------------------------------------------------------------
    # Step one
    # ------------------------------------------------------------------

    def fill_info(self, first_name: str, last_name: str, postal_code: str):
        self.type(self._FIRST_NAME, first_name)
        self.type(self._LAST_NAME, last_name)
        self.type(self._POSTAL_CODE, postal_code)
        self.click(self._CONTINUE_BTN)

    def cancel_step_one(self):
        self.click(self._CANCEL_BTN)

    def get_error_message(self) -> str:
        return self.get_text(self._ERROR_MSG)

    def is_error_displayed(self) -> bool:
        return self.is_visible(self._ERROR_MSG)

    # ------------------------------------------------------------------
    # Step two — overview
    # ------------------------------------------------------------------

    def get_overview_item_names(self) -> list[str]:
        return [el.text for el in self.driver.find_elements(*self._ITEM_NAMES)]

    def get_overview_item_prices(self) -> list[float]:
        return [
            float(el.text.replace("$", ""))
            for el in self.driver.find_elements(*self._ITEM_PRICES)
        ]

    def get_subtotal(self) -> float:
        text = self.get_text(self._SUBTOTAL)
        return float(text.split("$")[-1])

    def get_tax(self) -> float:
        text = self.get_text(self._TAX)
        return float(text.split("$")[-1])

    def get_total(self) -> float:
        text = self.get_text(self._TOTAL)
        return float(text.split("$")[-1])

    def finish(self):
        self.click(self._FINISH_BTN)

    def cancel_overview(self):
        self.click(self._CANCEL_OVERVIEW_BTN)

    # ------------------------------------------------------------------
    # Confirmation
    # ------------------------------------------------------------------

    def is_order_complete(self) -> bool:
        return self.is_visible(self._COMPLETE_HEADER)

    def get_complete_header_text(self) -> str:
        return self.get_text(self._COMPLETE_HEADER)

    def get_complete_body_text(self) -> str:
        return self.get_text(self._COMPLETE_TEXT)

    def go_back_home(self):
        self.click(self._BACK_HOME_BTN)

    def open_step_one(self):
        """Navigate directly to the checkout info page (bypassing cart).

        Does not wait for any specific element after the navigation — an
        unauthenticated request is redirected to the login page, so callers
        that need to assert on the landed page should wait themselves.
        """
        super().open(self.PATH_STEP_ONE)

    def get_field_value(self, locator) -> str:
        return self.driver.find_element(*locator).get_attribute("value")

    def get_first_name_value(self) -> str:
        return self.get_field_value(self._FIRST_NAME)

    def get_last_name_value(self) -> str:
        return self.get_field_value(self._LAST_NAME)

    def get_postal_code_value(self) -> str:
        return self.get_field_value(self._POSTAL_CODE)
