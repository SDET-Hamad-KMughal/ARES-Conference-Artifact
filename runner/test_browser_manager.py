"""Smoke test for the ARES BrowserManager."""

from runner.core.browser_manager import BrowserManager


def main() -> None:
    with BrowserManager(
        output_directory="runner/results/angular",
        headless=False,
    ) as browser:
        browser.open("http://localhost:4200/login")

        state = browser.capture_state(prefix="angular")

        print("State ID:", state.state_id)
        print("Title:", state.title)
        print("URL:", state.url)
        print("Screenshot:", state.screenshot_path)
        print("DOM:", state.dom_path)
        print("Metadata:", state.metadata_path)


if __name__ == "__main__":
    main()