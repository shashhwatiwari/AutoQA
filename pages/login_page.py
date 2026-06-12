from selenium.webdriver.common.by import By
from pages.base_page import BasePage


class LoginPage(BasePage):
    PATH = "/"

    _USERNAME = (By.ID, "user-name")
    _PASSWORD = (By.ID, "password")
    _LOGIN_BTN = (By.ID, "login-button")
    _ERROR_MSG = (By.CSS_SELECTOR, "[data-test='error']")
    _ERROR_CLOSE_BTN = (By.CLASS_NAME, "error-button")
    _LOGIN_LOGO = (By.CLASS_NAME, "login_logo")

    def open(self):
        super().open(self.PATH)
        self.wait_for_visible(self._LOGIN_BTN)

    def login(self, username: str, password: str):
        self.type(self._USERNAME, username)
        self.type(self._PASSWORD, password)
        self.click(self._LOGIN_BTN)

    def get_username_value(self) -> str:
        return self.driver.find_element(*self._USERNAME).get_attribute("value")

    def get_error_message(self) -> str:
        return self.get_text(self._ERROR_MSG)

    def is_error_displayed(self) -> bool:
        return self.is_visible(self._ERROR_MSG)

    def close_error(self):
        self.click(self._ERROR_CLOSE_BTN)

    def is_on_login_page(self) -> bool:
        return self.is_visible(self._LOGIN_BTN, timeout=5)

    def get_password_field_type(self) -> str:
        """Returns the `type` attribute of the password input (should be 'password')."""
        return self.driver.find_element(*self._PASSWORD).get_attribute("type")

    def get_username_field_type(self) -> str:
        return self.driver.find_element(*self._USERNAME).get_attribute("type")

    def tab_to_password_then_submit(self, username: str, password: str):
        """
        Navigate the form using only keyboard: fill username, TAB to password,
        fill password, TAB to button, ENTER to submit.
        Exercises tab-order and keyboard accessibility.
        """
        from selenium.webdriver.common.keys import Keys
        username_el = self.wait_for_visible(self._USERNAME)
        username_el.clear()
        username_el.send_keys(username)
        username_el.send_keys(Keys.TAB)          # focus moves to password
        self.driver.switch_to.active_element.send_keys(password)
        self.driver.switch_to.active_element.send_keys(Keys.TAB)  # focus to button
        self.driver.switch_to.active_element.send_keys(Keys.ENTER)
