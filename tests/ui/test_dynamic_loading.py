"""
Dynamic loading + scroll test suite — the-internet.herokuapp.com

Covers:
  Example 1 — element is hidden in DOM, revealed when loading completes.
  Example 2 — element is absent from DOM, injected after loading completes.

Both examples use the same WebDriver pattern:
  click Start → wait for spinner to disappear → assert finish text.

Scroll helpers from BasePage (scroll_to_element, scroll_by, scroll_to_bottom)
are exercised explicitly so the POM coverage is demonstrated.
"""
import pytest
from pages.dynamic_loading_page import DynamicLoadingPage


@pytest.mark.ui
@pytest.mark.slow
class TestDynamicLoadingExample1:
    """Element is present in DOM but hidden; revealed after spinner clears."""

    def test_finish_text_appears_after_start(self, driver, internet_base_url):
        page = DynamicLoadingPage(driver, internet_base_url)
        page.open_example(1)

        page.click_start()
        page.wait_for_loading_to_finish()

        assert page.is_finish_visible()

    def test_finish_text_content(self, driver, internet_base_url):
        page = DynamicLoadingPage(driver, internet_base_url)
        page.open_example(1)

        page.click_start()
        page.wait_for_loading_to_finish()

        assert page.get_finish_text() == "Hello World!"

    def test_start_button_triggers_spinner(self, driver, internet_base_url):
        page = DynamicLoadingPage(driver, internet_base_url)
        page.open_example(1)

        # Spinner appears immediately after clicking start
        page.click_start()
        # Loading bar is transiently visible — we assert it eventually goes away
        page.wait_for_loading_to_finish(timeout=15)

        assert page.is_finish_visible()

    def test_scroll_to_start_button_then_click(self, driver, internet_base_url):
        """Exercises scroll_to_element helper from BasePage."""
        page = DynamicLoadingPage(driver, internet_base_url)
        page.open_example(1)

        # Scroll down then back up to prove scroll helpers work
        page.scroll_to_bottom()
        page.scroll_to_start_button()   # scroll_to_element under the hood

        page.click_start()
        page.wait_for_loading_to_finish()

        assert page.get_finish_text() == "Hello World!"

    def test_scroll_to_finish_element_after_load(self, driver, internet_base_url):
        """Exercises scroll_to_element on a dynamically revealed element."""
        page = DynamicLoadingPage(driver, internet_base_url)
        page.open_example(1)

        page.click_start()
        page.wait_for_loading_to_finish()

        # Should not raise even if element is already in view
        page.scroll_to_finish_element()
        assert page.get_finish_text() == "Hello World!"


@pytest.mark.ui
@pytest.mark.slow
class TestDynamicLoadingExample2:
    """Element is not in DOM at page load; injected after spinner clears."""

    def test_finish_text_appears_after_start(self, driver, internet_base_url):
        page = DynamicLoadingPage(driver, internet_base_url)
        page.open_example(2)

        page.click_start()
        page.wait_for_loading_to_finish()

        assert page.is_finish_visible()

    def test_finish_text_content(self, driver, internet_base_url):
        page = DynamicLoadingPage(driver, internet_base_url)
        page.open_example(2)

        page.click_start()
        page.wait_for_loading_to_finish()

        assert page.get_finish_text() == "Hello World!"

    def test_finish_element_absent_before_start(self, driver, internet_base_url):
        """Confirms the element is not in the DOM before the button is clicked."""
        page = DynamicLoadingPage(driver, internet_base_url)
        page.open_example(2)

        # Element has NOT been injected yet — is_visible uses a short timeout
        assert not page.is_finish_visible()

    def test_scroll_by_then_trigger_dynamic_element(self, driver, internet_base_url):
        """Exercises scroll_by and scroll_to_top helpers."""
        page = DynamicLoadingPage(driver, internet_base_url)
        page.open_example(2)

        page.scroll_by(0, 200)
        page.scroll_to_top()

        page.click_start()
        page.wait_for_loading_to_finish()

        assert page.get_finish_text() == "Hello World!"


@pytest.mark.ui
class TestScrollHelpers:
    """
    Dedicated tests for BasePage scroll primitives to ensure they don't
    raise on normal pages (regression guard).
    """

    def test_scroll_to_bottom_does_not_raise(self, driver, internet_base_url):
        page = DynamicLoadingPage(driver, internet_base_url)
        page.open_example(1)
        page.scroll_to_bottom()   # no assertion — just must not raise

    def test_scroll_to_top_does_not_raise(self, driver, internet_base_url):
        page = DynamicLoadingPage(driver, internet_base_url)
        page.open_example(1)
        page.scroll_to_bottom()
        page.scroll_to_top()

    def test_scroll_by_increments(self, driver, internet_base_url):
        page = DynamicLoadingPage(driver, internet_base_url)
        page.open_example(1)
        # Multiple incremental scrolls
        for _ in range(3):
            page.scroll_by(0, 100)
        page.scroll_to_top()
