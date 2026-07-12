"""Smoke test for the ARES DOMAnalyzer."""

from pathlib import Path
from typing import Any, Dict

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from runner.core.browser_manager import BrowserManager
from runner.core.dom_analyzer import DOMAnalyzer


ANGULAR_LOGIN_URL = "http://localhost:4200/catalog"

OUTPUT_DIRECTORY = Path("runner/results/angular")
OUTPUT_PATH = OUTPUT_DIRECTORY / "dom_analysis.json"


def wait_for_angular(browser) -> None:
    """
    Wait until Angular has rendered real page content.
    """

    driver = browser.driver
    wait = WebDriverWait(driver, 20)

    wait.until(
        lambda current_driver:
        current_driver.execute_script(
            "return document.readyState"
        ) == "complete"
    )

    wait.until(
        lambda current_driver:
        current_driver.execute_script(
            """
            const root = document.querySelector('app-root');

            return Boolean(
                root &&
                root.children.length > 0 &&
                root.innerHTML.trim().length > 20
            );
            """
        )
    )

    wait.until(
        lambda current_driver:
        len(
            current_driver.find_elements(
                By.CSS_SELECTOR,
                (
                    "button, a[href], input, textarea, "
                    "select, form, [role='button']"
                ),
            )
        ) > 0
    )


def validate_analysis(
    result: Dict[str, Any],
    saved_path: Path,
) -> None:
    required_keys = {
        "title",
        "url",
        "timestamp",
        "buttons",
        "links",
        "inputs",
        "forms",
        "interactive_elements",
        "summary",
    }

    missing_keys = required_keys.difference(result.keys())

    assert not missing_keys, (
        f"Missing DOM analysis keys: {sorted(missing_keys)}"
    )

    assert result["url"].startswith(
        "http://localhost:4200"
    ), f"Unexpected URL: {result['url']}"

    assert result["summary"][
        "interactive_element_count"
    ] > 0, (
        "Angular loaded, but no interactive elements were found."
    )

    assert saved_path.exists(), (
        f"JSON file was not created: {saved_path}"
    )

    assert saved_path.stat().st_size > 0, (
        f"JSON file is empty: {saved_path}"
    )


def print_summary(
    result: Dict[str, Any],
    saved_path: Path,
) -> None:
    summary = result["summary"]

    print("=" * 60)
    print("ARES DOM Analyzer Smoke Test")
    print("=" * 60)
    print(f"Title: {result['title']}")
    print(f"URL: {result['url']}")
    print(f"Timestamp: {result['timestamp']}")
    print(f"Buttons: {summary['button_count']}")
    print(f"Links: {summary['link_count']}")
    print(f"Inputs: {summary['input_count']}")
    print(f"Forms: {summary['form_count']}")
    print(
        "Interactive elements: "
        f"{summary['interactive_element_count']}"
    )
    print(f"JSON saved: {saved_path}")
    print("=" * 60)


def main() -> None:
    with BrowserManager(
        output_directory=str(OUTPUT_DIRECTORY),
        headless=False,
    ) as browser:
        browser.open(ANGULAR_LOGIN_URL)

        try:
            wait_for_angular(browser)

        except TimeoutException:
            driver = browser.driver

            print("Angular did not render within 20 seconds.")
            print("Current URL:", driver.current_url)
            print("Page title:", driver.title)
            print(
                "Body HTML:",
                driver.execute_script(
                    "return document.body.innerHTML;"
                ),
            )

            try:
                print("Browser console logs:")

                for entry in driver.get_log("browser"):
                    print(entry)

            except Exception:
                print(
                    "Browser console logs are unavailable."
                )

            raise

        analyzer = DOMAnalyzer(browser.driver)
        result = analyzer.analyze()
        saved_path = analyzer.save_json(OUTPUT_PATH)

        validate_analysis(result, saved_path)
        print_summary(result, saved_path)

        print("DOM analyzer test passed.")


if __name__ == "__main__":
    main()