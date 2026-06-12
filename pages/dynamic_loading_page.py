from selenium.webdriver.common.by import By
from pages.base_page import BasePage


class DynamicLoadingPage(BasePage):
    """
    Covers both example variants on the-internet.herokuapp.com:
      Example 1 — element hidden, revealed after click
      Example 2 — element not in DOM, injected after click
    """

    PATH_EXAMPLE_1 = "/dynamic_loading/1"
    PATH_EXAMPLE_2 = "/dynamic_loading/2"

    _START_BTN = (By.CSS_SELECTOR, "#start button")
    _LOADING_BAR = (By.ID, "loading")
    _FINISH_TEXT = (By.CSS_SELECTOR, "#finish h4")

    def open_example(self, number: int):
        """number: 1 or 2"""
        super().open(f"/dynamic_loading/{number}")
        self.wait_for_visible(self._START_BTN)

    def click_start(self):
        self.click(self._START_BTN)

    def wait_for_loading_to_finish(self, timeout: int = 15):
        """Wait for the spinner to disappear, then wait for the result text."""
        self.wait_for_invisible(self._LOADING_BAR, timeout=timeout)

    def get_finish_text(self) -> str:
        return self.get_text(self._FINISH_TEXT)

    def is_finish_visible(self) -> bool:
        return self.is_visible(self._FINISH_TEXT, timeout=15)

    # ------------------------------------------------------------------
    # Scroll-trigger helper — used by tests that scroll the page to
    # demonstrate scroll_to_element / scroll_by coverage.
    # ------------------------------------------------------------------

    def scroll_to_start_button(self):
        self.scroll_to_element(self._START_BTN)

    def scroll_to_finish_element(self):
        self.scroll_to_element(self._FINISH_TEXT)
