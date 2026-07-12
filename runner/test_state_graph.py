"""Smoke test for the ARES StateGraph."""

from pathlib import Path

from runner.core.action_executor import ActionExecutor
from runner.core.browser_manager import BrowserManager
from runner.core.dom_analyzer import DOMAnalyzer
from runner.core.state_graph import StateGraph


OUTPUT_DIRECTORY = Path(
    "runner/results/angular"
)

OUTPUT_PATH = OUTPUT_DIRECTORY / "state_graph.json"

START_URL = "http://localhost:4200/login"


def main() -> None:
    """
    Build a two-state graph using the Angular SUT.
    """

    graph = StateGraph()

    with BrowserManager(
        output_directory=str(OUTPUT_DIRECTORY),
        headless=False,
    ) as browser:
        browser.open(START_URL)

        analyzer = DOMAnalyzer(
            browser.driver
        )

        login_analysis = analyzer.analyze()

        login_state = graph.add_state(
            login_analysis,
            metadata={
                "sut": "angular",
                "page": "login",
            },
        )

        actions = ActionExecutor(browser)

        actions.click_css(
            'a[href="/catalog"]'
        )

        catalog_analysis = analyzer.analyze()

        catalog_state = graph.add_state(
            catalog_analysis,
            metadata={
                "sut": "angular",
                "page": "catalog",
            },
        )

        graph.add_transition(
            source_state_id=login_state.state_id,
            target_state_id=catalog_state.state_id,
            action_type="click",
            action_target='a[href="/catalog"]',
            metadata={
                "description": (
                    "Navigate from login to catalog"
                )
            },
        )

        saved_path = graph.save_json(
            OUTPUT_PATH
        )

        summary = graph.summary()

        print("=" * 60)
        print("ARES State Graph Smoke Test")
        print("=" * 60)
        print(
            f"Login state: {login_state.state_id}"
        )
        print(
            f"Catalog state: {catalog_state.state_id}"
        )
        print(
            f"Nodes: {summary['node_count']}"
        )
        print(
            f"Edges: {summary['edge_count']}"
        )
        print(
            f"JSON saved: {saved_path}"
        )
        print("=" * 60)

        assert summary["node_count"] == 2, (
            "Expected two states."
        )

        assert summary["edge_count"] == 1, (
            "Expected one transition."
        )

        assert saved_path.exists(), (
            f"State graph file not created: "
            f"{saved_path}"
        )

        print("State graph test passed.")


if __name__ == "__main__":
    main()