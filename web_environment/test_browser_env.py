from pathlib import Path

from selenium.webdriver.common.by import By

from web_environment.browser_env import BrowserEnvironment


def main() -> None:
    screenshot_path = Path("results/browser_environment/example.png")

    with BrowserEnvironment(headless=False) as browser:
        browser.open("https://example.com")

        print("Title:", browser.page_title())
        print("URL:", browser.current_url())

        browser.scroll_by(y=300)
        browser.screenshot(screenshot_path)

        browser.click(By.CSS_SELECTOR, "a")

        print("Navigation successful:", browser.current_url())


if __name__ == "__main__":
    main()
