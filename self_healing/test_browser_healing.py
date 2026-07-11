"""Real-browser test for the ARES self-healing engine."""

from __future__ import annotations

from pathlib import Path

from selenium.webdriver.common.by import By

from self_healing.healer import LocatorHealer
from web_environment.browser_env import BrowserEnvironment
from web_environment.dom_extractor import DOMExtractor


HTML_VERSION_1 = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>ARES Healing Test</title>
</head>
<body>
    <main>
        <form>
            <button
                id="login-button"
                name="login"
                type="submit"
                aria-label="Sign in"
                class="btn btn-primary">
                Sign in
            </button>

            <a
                id="support-link"
                href="/support"
                aria-label="Contact support">
                Contact support
            </a>
        </form>
    </main>
</body>
</html>
"""


HTML_VERSION_2 = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>ARES Healing Test</title>
</head>
<body>
    <main>
        <section>
            <form>
                <button
                    id="signin-button"
                    name="login"
                    type="submit"
                    aria-label="Log in"
                    class="btn primary-button">
                    Log in
                </button>

                <a
                    id="support-link"
                    href="/support"
                    aria-label="Contact support">
                    Contact support
                </a>
            </form>
        </section>
    </main>
</body>
</html>
"""


def write_html(path: Path, content: str) -> None:
    """Write an HTML test page."""
    path.write_text(content, encoding="utf-8")


def find_by_id(
    elements: list[dict],
    element_id: str,
) -> dict:
    """Return one extracted element by ID."""
    for element in elements:
        if element.get("id") == element_id:
            return element

    raise RuntimeError(f"Element not found: {element_id}")


def main() -> None:
    test_directory = Path("results/healing_test")
    test_directory.mkdir(parents=True, exist_ok=True)

    version_1_path = test_directory / "page_v1.html"
    version_2_path = test_directory / "page_v2.html"

    write_html(version_1_path, HTML_VERSION_1)
    write_html(version_2_path, HTML_VERSION_2)

    with BrowserEnvironment(headless=False) as browser:
        extractor = DOMExtractor(browser.driver)

        browser.open(version_1_path.resolve().as_uri())

        original_elements = extractor.extract_interactive_elements()

        original_element = find_by_id(
            original_elements,
            "login-button",
        )

        print("Original locator:", original_element["id"])
        print("Original text:", original_element["text"])

        browser.open(version_2_path.resolve().as_uri())

        new_elements = extractor.extract_interactive_elements()

        try:
            browser.click(By.ID, "login-button")
            old_locator_failed = False
        except Exception:
            old_locator_failed = True

        print("Old locator failed:", old_locator_failed)

        driver = browser.driver

        if driver is None:
            raise RuntimeError("Browser driver is not available.")

        viewport_width = driver.execute_script(
            "return window.innerWidth;"
        )

        viewport_height = driver.execute_script(
            "return window.innerHeight;"
        )

        healer = LocatorHealer(threshold=0.7)

        result = healer.heal(
            original_element=original_element,
            candidates=new_elements,
            viewport_width=float(viewport_width),
            viewport_height=float(viewport_height),
        )

        print("Healed:", result.healed)
        print("Selected score:", result.selected_score)
        print("Replacement locator:", result.replacement_locator)
        print("Reason:", result.reason)

        assert old_locator_failed is True
        assert result.healed is True
        assert result.selected_candidate is not None
        assert result.selected_candidate["id"] == "signin-button"

        replacement = result.replacement_locator

        if replacement is None:
            raise RuntimeError("No replacement locator was generated.")

        strategy = replacement["strategy"]
        value = replacement["value"]

        if strategy == "id":
            browser.click(By.ID, value)
        elif strategy == "name":
            browser.click(By.NAME, value)
        elif strategy == "css selector":
            browser.click(By.CSS_SELECTOR, value)
        elif strategy == "xpath":
            browser.click(By.XPATH, value)
        else:
            raise RuntimeError(
                f"Unsupported locator strategy: {strategy}"
            )

        print("Replacement locator executed successfully.")
        print("Real-browser healing test passed.")


if __name__ == "__main__":
    main()