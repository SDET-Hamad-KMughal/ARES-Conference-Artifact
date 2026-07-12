"""Smoke test for the ARES ActionExecutor."""

from runner.core.action_executor import ActionExecutor
from runner.core.browser_manager import BrowserManager


def main() -> None:
    with BrowserManager(
        output_directory="runner/results/action_test",
        headless=False,
    ) as browser:
        browser.open("http://localhost:4200/login")

        actions = ActionExecutor(browser)

        before = browser.capture_state("before")
        print("Before:", before.url)

        actions.click_css('a[href="/catalog"]')

        after = browser.capture_state("after")
        print("After:", after.url)

        assert "/catalog" in after.url
        print("Action executor test passed.")


if __name__ == "__main__":
    main()