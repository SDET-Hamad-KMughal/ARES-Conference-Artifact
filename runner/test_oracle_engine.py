"""Smoke test for the ARES OracleEngine."""

from pathlib import Path
from typing import Any, Dict

from selenium.webdriver.support.ui import WebDriverWait

from runner.core.action_executor import ActionExecutor
from runner.core.browser_manager import BrowserManager
from runner.core.oracle_engine import OracleEngine


START_URL = "http://localhost:4200/login"

OUTPUT_DIRECTORY = Path(
    "runner/results/angular"
)


def wait_for_angular(browser: BrowserManager) -> None:
    """
    Wait until Angular has rendered the page.
    """

    WebDriverWait(
        browser.driver,
        20,
    ).until(
        lambda driver: driver.execute_script(
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


def print_result(
    result: Dict[str, Any],
) -> None:
    """
    Print the oracle result.
    """

    print("=" * 60)
    print("ARES Oracle Engine Smoke Test")
    print("=" * 60)
    print(
        f"Expected URL: {result['expected_url']}"
    )
    print(
        f"Actual URL: {result['actual_url']}"
    )
    print(
        f"Expected text: {result['expected_text']}"
    )
    print(
        f"URL match: {result['url_match']}"
    )
    print(
        "Success text found: "
        f"{result['success_text_found']}"
    )
    print(
        f"Error detected: {result['error_detected']}"
    )
    print(
        f"Detected errors: {result['detected_errors']}"
    )
    print(
        f"Score: {result['score']}"
    )
    print(
        f"Reason: {result['reason']}"
    )
    print(
        f"Overall: "
        f"{'PASS' if result['passed'] else 'FAIL'}"
    )
    print("=" * 60)


def main() -> None:
    """
    Test the Oracle Engine after navigating to the catalog page.
    """

    with BrowserManager(
        output_directory=str(
            OUTPUT_DIRECTORY
        ),
        headless=False,
    ) as browser:
        browser.open(START_URL)

        wait_for_angular(browser)

        actions = ActionExecutor(browser)

        actions.click_css(
            'a[href="/catalog"]'
        )

        WebDriverWait(
            browser.driver,
            20,
        ).until(
            lambda driver:
            "/catalog" in driver.current_url
        )

        oracle = OracleEngine()

        result = oracle.evaluate(
            driver=browser.driver,
            expected_url="/catalog",
            expected_text="Catalog",
        )

        print_result(result)

        assert result["passed"], (
            f"Oracle evaluation failed: "
            f"{result['reason']}"
        )

        assert result["url_match"] is True, (
            "Expected URL oracle to pass."
        )

        assert (
            result["success_text_found"] is True
        ), (
            "Expected success-text oracle to pass."
        )

        assert (
            result["error_detected"] is False
        ), (
            "Expected no page errors."
        )

        print("Oracle engine test passed.")


if __name__ == "__main__":
    main()