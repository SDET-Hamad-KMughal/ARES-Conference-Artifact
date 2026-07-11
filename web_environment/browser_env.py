"""Reusable Selenium browser environment for ARES."""

from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BrowserEnvironment:
    """Controls the Selenium browser used by ARES."""

    def __init__(
        self,
        headless: bool = False,
        timeout: int = 15,
        width: int = 1440,
        height: int = 900,
    ) -> None:
        self.headless = headless
        self.timeout = timeout
        self.width = width
        self.height = height
        self.driver: Optional[WebDriver] = None

    def start(self) -> WebDriver:
        """Start a Chrome browser session."""
        if self.driver is not None:
            return self.driver

        options = ChromeOptions()

        if self.headless:
            options.add_argument("--headless=new")

        options.add_argument(f"--window-size={self.width},{self.height}")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")

        self.driver = webdriver.Chrome(options=options)
        self.driver.set_page_load_timeout(self.timeout)

        return self.driver

    def open(self, url: str) -> None:
        """Open a URL."""
        self._require_driver().get(url)

    def screenshot(self, output_path: str) -> Path:
        """Save the current browser screenshot."""
        driver = self._require_driver()

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if not driver.save_screenshot(str(path)):
            raise RuntimeError(f"Could not save screenshot: {path}")

        return path

    def current_url(self) -> str:
        """Return the current URL."""
        return self._require_driver().current_url

    def page_title(self) -> str:
        """Return the current page title."""
        return self._require_driver().title

    def page_source(self) -> str:
        """Return the current DOM source."""
        return self._require_driver().page_source

    def scroll_by(self, x: int = 0, y: int = 600) -> None:
        """
        Scroll the current page.

        Parameters
        ----------
        x : int
            Horizontal scroll amount.
        y : int
            Vertical scroll amount.
        """
        driver = self._require_driver()
        driver.execute_script(
            "window.scrollBy(arguments[0], arguments[1]);",
            x,
            y,
        )

    def click(self, by: By, locator: str) -> None:
        """
        Click an element after waiting for it to become clickable.
        """
        driver = self._require_driver()

        element = WebDriverWait(driver, self.timeout).until(
            EC.element_to_be_clickable((by, locator))
        )

        element.click()

    def back(self) -> None:
        """Navigate backward."""
        self._require_driver().back()

    def forward(self) -> None:
        """Navigate forward."""
        self._require_driver().forward()

    def refresh(self) -> None:
        """Refresh the current page."""
        self._require_driver().refresh()

    def close(self) -> None:
        """Close the browser safely."""
        if self.driver is not None:
            try:
                self.driver.quit()
            except WebDriverException:
                pass
            finally:
                self.driver = None

    def _require_driver(self) -> WebDriver:
        """Return the active driver."""
        if self.driver is None:
            raise RuntimeError("Call start() before using the browser.")

        return self.driver

    def __enter__(self) -> "BrowserEnvironment":
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()