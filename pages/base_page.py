from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains


class BasePage:
    DEFAULT_TIMEOUT = 10

    def __init__(self, driver, base_url: str):
        self.driver = driver
        self.base_url = base_url
        self.wait = WebDriverWait(driver, self.DEFAULT_TIMEOUT)

    def open(self, path: str = ""):
        self.driver.get(f"{self.base_url}{path}")

    # ------------------------------------------------------------------
    # Waits
    # ------------------------------------------------------------------

    def wait_for_visible(self, locator, timeout=None):
        t = timeout or self.DEFAULT_TIMEOUT
        return WebDriverWait(self.driver, t).until(
            EC.visibility_of_element_located(locator)
        )

    def wait_for_clickable(self, locator, timeout=None):
        t = timeout or self.DEFAULT_TIMEOUT
        return WebDriverWait(self.driver, t).until(
            EC.element_to_be_clickable(locator)
        )

    def wait_for_invisible(self, locator, timeout=None):
        t = timeout or self.DEFAULT_TIMEOUT
        return WebDriverWait(self.driver, t).until(
            EC.invisibility_of_element_located(locator)
        )

    def wait_for_url_contains(self, fragment, timeout=None):
        t = timeout or self.DEFAULT_TIMEOUT
        WebDriverWait(self.driver, t).until(EC.url_contains(fragment))

    def wait_for_text_in_element(self, locator, text: str, timeout=None) -> bool:
        t = timeout or self.DEFAULT_TIMEOUT
        return WebDriverWait(self.driver, t).until(
            EC.text_to_be_present_in_element(locator, text)
        )

    def wait_for_element_count(self, locator, count: int, timeout=None):
        """Block until at least `count` elements match the locator."""
        t = timeout or self.DEFAULT_TIMEOUT
        WebDriverWait(self.driver, t).until(
            lambda d: len(d.find_elements(*locator)) >= count
        )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def click(self, locator):
        self.wait_for_clickable(locator).click()

    def safe_click(self, locator):
        """JavaScript click — use when a normal click is intercepted by an overlay."""
        el = self.wait_for_visible(locator)
        self.driver.execute_script("arguments[0].click();", el)

    def type(self, locator, text: str, clear: bool = True):
        el = self.wait_for_visible(locator)
        if clear:
            el.clear()
        try:
            el.send_keys(text)
        except Exception:
            # ChromeDriver cannot send non-BMP characters (emoji, supplementary
            # Unicode plane) via send_keys. Fall back to a JS assignment so the
            # field receives the value and downstream assertions still work.
            self.driver.execute_script("arguments[0].value = arguments[1];", el, text)

    def get_text(self, locator) -> str:
        return self.wait_for_visible(locator).text

    def is_visible(self, locator, timeout: int = 3) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            return True
        except Exception:
            return False

    def hover(self, locator):
        el = self.wait_for_visible(locator)
        ActionChains(self.driver).move_to_element(el).perform()

    # ------------------------------------------------------------------
    # Scroll
    # ------------------------------------------------------------------

    def scroll_to_element(self, locator):
        """Scroll the locator into the viewport and return the element."""
        el = self.wait_for_visible(locator)
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        return el

    def scroll_into_view(self, element):
        """Scroll a WebElement (already found) into view."""
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)

    def scroll_to_bottom(self):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    def scroll_to_top(self):
        self.driver.execute_script("window.scrollTo(0, 0);")

    def scroll_by(self, x: int = 0, y: int = 300):
        self.driver.execute_script(f"window.scrollBy({x}, {y});")

    # ------------------------------------------------------------------
    # Cookies / session
    # ------------------------------------------------------------------

    def get_cookies(self) -> dict:
        return {c["name"]: c["value"] for c in self.driver.get_cookies()}

    def get_cookie(self, name: str):
        return self.driver.get_cookie(name)

    def add_cookie(self, name: str, value: str):
        self.driver.add_cookie({"name": name, "value": value})

    def delete_cookie(self, name: str):
        self.driver.delete_cookie(name)

    def delete_all_cookies(self):
        self.driver.delete_all_cookies()

    def get_local_storage_item(self, key: str):
        return self.driver.execute_script(
            f"return window.localStorage.getItem('{key}');"
        )

    def set_local_storage_item(self, key: str, value: str):
        self.driver.execute_script(
            f"window.localStorage.setItem('{key}', '{value}');"
        )

    def clear_local_storage(self):
        self.driver.execute_script("window.localStorage.clear();")

    # ------------------------------------------------------------------
    # Page info
    # ------------------------------------------------------------------

    @property
    def title(self) -> str:
        return self.driver.title

    @property
    def current_url(self) -> str:
        return self.driver.current_url

    def get_page_source(self) -> str:
        return self.driver.page_source
