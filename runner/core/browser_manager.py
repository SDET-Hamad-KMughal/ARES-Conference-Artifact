"""Browser session management for ARES experiments."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver import ChromeOptions
from selenium.webdriver.remote.webdriver import WebDriver


@dataclass
class BrowserState:
    """Captured state of the current browser page."""

    state_id: str
    url: str
    title: str
    screenshot_path: str
    dom_path: str
    metadata_path: str
    captured_at: str


class BrowserManager:
    """Start, control, and capture a Selenium browser session."""

    def __init__(
        self,
        output_directory: str = "runner/results/browser_states",
        headless: bool = False,
        timeout: int = 30,
        width: int = 1440,
        height: int = 900,
        accept_insecure_certificates: bool = True,
    ) -> None:
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)

        self.headless = headless
        self.timeout = timeout
        self.width = width
        self.height = height
        self.accept_insecure_certificates = accept_insecure_certificates

        self.driver: Optional[WebDriver] = None
        self._state_counter = 0

    def start(self) -> WebDriver:
        """Start Chrome if no active browser session exists."""
        if self.driver is not None:
            return self.driver

        options = ChromeOptions()

        if self.headless:
            options.add_argument("--headless=new")

        options.add_argument(
            f"--window-size={self.width},{self.height}"
        )
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")

        options.accept_insecure_certs = self.accept_insecure_certificates

        self.driver = webdriver.Chrome(options=options)
        self.driver.set_page_load_timeout(self.timeout)

        return self.driver

    def open(self, url: str) -> None:
        """Open a target URL."""
        driver = self._require_driver()
        driver.get(url)

    def capture_state(self, prefix: str = "state") -> BrowserState:
        """Capture screenshot, DOM, URL, title, and metadata."""
        driver = self._require_driver()

        self._state_counter += 1
        state_id = f"{prefix}_{self._state_counter:04d}"

        screenshot_path = self.output_directory / f"{state_id}.png"
        dom_path = self.output_directory / f"{state_id}.html"
        metadata_path = self.output_directory / f"{state_id}.json"

        screenshot_saved = driver.save_screenshot(str(screenshot_path))

        if not screenshot_saved:
            raise RuntimeError(
                f"Could not save screenshot to {screenshot_path}"
            )

        dom_path.write_text(
            driver.page_source,
            encoding="utf-8",
        )

        state = BrowserState(
            state_id=state_id,
            url=driver.current_url,
            title=driver.title,
            screenshot_path=str(screenshot_path),
            dom_path=str(dom_path),
            metadata_path=str(metadata_path),
            captured_at=datetime.now(timezone.utc).isoformat(),
        )

        metadata_path.write_text(
            json.dumps(asdict(state), indent=2),
            encoding="utf-8",
        )

        return state

    def current_url(self) -> str:
        """Return the current browser URL."""
        return self._require_driver().current_url

    def title(self) -> str:
        """Return the current page title."""
        return self._require_driver().title

    def refresh(self) -> None:
        """Refresh the current page."""
        self._require_driver().refresh()

    def back(self) -> None:
        """Navigate backward."""
        self._require_driver().back()

    def close(self) -> None:
        """Close the browser session safely."""
        if self.driver is None:
            return

        try:
            self.driver.quit()
        except WebDriverException:
            pass
        finally:
            self.driver = None

    def _require_driver(self) -> WebDriver:
        """Return the active driver or raise a clear error."""
        if self.driver is None:
            raise RuntimeError(
                "Browser is not running. Call start() first."
            )

        return self.driver

    def __enter__(self) -> "BrowserManager":
        self.start()
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        self.close()