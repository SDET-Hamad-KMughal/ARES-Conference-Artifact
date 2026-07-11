from web_environment.browser_env import BrowserEnvironment
from web_environment.dom_extractor import DOMExtractor


def main() -> None:
    with BrowserEnvironment(headless=False) as browser:
        browser.open("https://example.com")

        extractor = DOMExtractor(browser.driver)

        visible_elements = extractor.extract_visible_elements()
        interactive_elements = extractor.extract_interactive_elements()

        print("Visible elements:", len(visible_elements))
        print("Interactive elements:", len(interactive_elements))

        for element in interactive_elements[:10]:
            print(
                element["tag"],
                element["text"],
                element["xpath"],
                element["css_selector"],
            )


if __name__ == "__main__":
    main()