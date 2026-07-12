"""Smoke test for the ARES LogicEngine."""

from pathlib import Path
from typing import Any, Dict, List

from selenium.webdriver.support.ui import WebDriverWait

from runner.core.browser_manager import BrowserManager
from runner.core.dom_analyzer import DOMAnalyzer
from runner.core.logic_engine import LogicEngine


ANGULAR_URL = "http://localhost:4200/catalog"

OUTPUT_DIRECTORY = Path(
    "runner/results/angular"
)


def wait_for_page(browser) -> None:
    """
    Wait until Angular has rendered interactive content.
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


def print_actions(
    actions: List[Dict[str, Any]],
) -> None:
    """
    Print inferred actions in a readable format.
    """

    print("=" * 70)
    print("ARES Logic Engine Smoke Test")
    print("=" * 70)

    for index, action in enumerate(
        actions,
        start=1,
    ):
        print(
            f"{index}. "
            f"{action['action_type'].upper()}"
        )
        print(
            f"   Label: {action['label']}"
        )
        print(
            f"   Selector: {action['selector']}"
        )
        print(
            f"   Source: {action['source']}"
        )
        print(
            f"   Priority: {action['priority']}"
        )
        print("-" * 70)

    print(f"Total actions: {len(actions)}")
    print("=" * 70)


def main() -> None:
    """
    Run the Logic Engine against the Angular SUT.
    """

    with BrowserManager(
        output_directory=str(
            OUTPUT_DIRECTORY
        ),
        headless=False,
    ) as browser:
        browser.open(ANGULAR_URL)

        wait_for_page(browser)

        analyzer = DOMAnalyzer(
            browser.driver
        )

        analysis = analyzer.analyze()

        engine = LogicEngine()

        actions = engine.infer_actions(
            analysis
        )

        print_actions(actions)

        assert actions, (
            "Logic Engine inferred no actions."
        )

        assert any(
            action["action_type"] == "click"
            for action in actions
        ), (
            "Expected at least one click action."
        )

        assert any(
            action["source"] == "link"
            for action in actions
        ), (
            "Expected at least one link action."
        )

        print("Logic engine test passed.")


if __name__ == "__main__":
    main()