"""ARES end-to-end experiment runner.

This module coordinates the BrowserManager, DOMAnalyzer, LogicEngine,
ActionExecutor, OracleEngine, and StateGraph to execute a lightweight,
reproducible exploration experiment.
"""

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from selenium.webdriver.support.ui import WebDriverWait

from runner.core.action_executor import ActionExecutor
from runner.core.browser_manager import BrowserManager
from runner.core.dom_analyzer import DOMAnalyzer
from runner.core.logic_engine import LogicEngine
from runner.core.oracle_engine import OracleEngine
from runner.core.state_graph import StateGraph


@dataclass
class ExperimentStep:
    """
    Represents one action and its observed outcome.
    """

    step_number: int
    source_state_id: str
    target_state_id: str
    action_type: str
    action_label: str
    action_selector: str
    source_url: str
    target_url: str
    oracle_passed: bool
    oracle_score: float
    oracle_reason: str
    duration_seconds: float
    timestamp: str


@dataclass
class ExperimentResult:
    """
    Represents the complete result of one ARES experiment.
    """

    experiment_name: str
    sut_name: str
    start_url: str
    started_at: str
    completed_at: str
    duration_seconds: float
    status: str
    actions_inferred: int
    actions_executed: int
    successful_actions: int
    failed_actions: int
    states_discovered: int
    transitions_created: int
    oracle_pass_rate: float
    steps: List[Dict[str, Any]] = field(
        default_factory=list
    )
    errors: List[str] = field(
        default_factory=list
    )


class ExperimentRunner:
    """
    Coordinate an end-to-end ARES exploration experiment.
    """

    def __init__(
        self,
        sut_name: str,
        start_url: str,
        output_directory: str | Path,
        headless: bool = False,
        wait_timeout: int = 20,
    ) -> None:
        """
        Initialize the experiment runner.

        Args:
            sut_name: Human-readable system-under-test name.
            start_url: Initial browser URL.
            output_directory: Directory for generated experiment results.
            headless: Whether the browser should run without a visible window.
            wait_timeout: Maximum Selenium wait time in seconds.
        """

        self.sut_name = sut_name
        self.start_url = start_url
        self.output_directory = Path(
            output_directory
        )
        self.headless = headless
        self.wait_timeout = wait_timeout

        self.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.graph = StateGraph()
        self.logic_engine = LogicEngine()
        self.oracle_engine = OracleEngine()

    def run_route_experiment(
        self,
        experiment_name: str,
        route_sequence: List[str],
    ) -> Dict[str, Any]:
        """
        Execute a deterministic route-based exploration experiment.

        Each route is selected from LogicEngine candidate actions and executed
        through ActionExecutor. The resulting page is evaluated by OracleEngine
        and recorded in StateGraph.

        Args:
            experiment_name: Name of this experiment.
            route_sequence: Ordered application routes, such as
                ["/catalog", "/cart", "/checkout", "/success"].

        Returns:
            JSON-serializable experiment result dictionary.
        """

        started_at = datetime.now(
            timezone.utc
        )

        overall_start = time.perf_counter()

        steps: List[ExperimentStep] = []
        errors: List[str] = []

        actions_inferred = 0
        actions_executed = 0
        successful_actions = 0
        failed_actions = 0

        status = "completed"

        with BrowserManager(
            output_directory=str(
                self.output_directory
            ),
            headless=self.headless,
        ) as browser:
            browser.open(self.start_url)

            self._wait_for_angular(browser)

            analyzer = DOMAnalyzer(
                browser.driver
            )

            executor = ActionExecutor(browser)

            current_analysis = analyzer.analyze()

            current_state = self.graph.add_state(
                current_analysis,
                metadata={
                    "sut": self.sut_name,
                    "step": 0,
                    "role": "initial",
                },
            )

            for step_number, target_route in enumerate(
                route_sequence,
                start=1,
            ):
                step_start = time.perf_counter()

                source_analysis = current_analysis
                source_state = current_state
                source_url = source_analysis["url"]

                candidate_actions = (
                    self.logic_engine.infer_actions(
                        source_analysis
                    )
                )

                actions_inferred += len(
                    candidate_actions
                )

                selected_action = self._select_route_action(
                    actions=candidate_actions,
                    target_route=target_route,
                )

                if selected_action is None:
                    message = (
                        f"No candidate action found for route "
                        f"{target_route} from {source_url}"
                    )

                    errors.append(message)
                    failed_actions += 1
                    status = "failed"
                    break

                try:
                    executor.click_css(
                        selected_action["selector"]
                    )

                    actions_executed += 1

                    self._wait_for_route(
                        browser=browser,
                        expected_route=target_route,
                    )

                    self._wait_for_angular(browser)

                    current_analysis = analyzer.analyze()

                    current_state = self.graph.add_state(
                        current_analysis,
                        metadata={
                            "sut": self.sut_name,
                            "step": step_number,
                            "route": target_route,
                        },
                    )

                    oracle_result = (
                        self.oracle_engine.evaluate(
                            driver=browser.driver,
                            expected_url=target_route,
                            expected_text=self._route_text(
                                target_route
                            ),
                        )
                    )

                    self.graph.add_transition(
                        source_state_id=(
                            source_state.state_id
                        ),
                        target_state_id=(
                            current_state.state_id
                        ),
                        action_type=(
                            selected_action[
                                "action_type"
                            ]
                        ),
                        action_target=(
                            selected_action[
                                "selector"
                            ]
                        ),
                        metadata={
                            "label": selected_action[
                                "label"
                            ],
                            "target_route":
                                target_route,
                            "oracle_passed":
                                oracle_result[
                                    "passed"
                                ],
                            "oracle_score":
                                oracle_result[
                                    "score"
                                ],
                        },
                    )

                    if oracle_result["passed"]:
                        successful_actions += 1
                    else:
                        failed_actions += 1

                    step_duration = (
                        time.perf_counter()
                        - step_start
                    )

                    steps.append(
                        ExperimentStep(
                            step_number=step_number,
                            source_state_id=(
                                source_state.state_id
                            ),
                            target_state_id=(
                                current_state.state_id
                            ),
                            action_type=(
                                selected_action[
                                    "action_type"
                                ]
                            ),
                            action_label=(
                                selected_action["label"]
                            ),
                            action_selector=(
                                selected_action[
                                    "selector"
                                ]
                            ),
                            source_url=source_url,
                            target_url=(
                                current_analysis["url"]
                            ),
                            oracle_passed=(
                                oracle_result["passed"]
                            ),
                            oracle_score=(
                                oracle_result["score"]
                            ),
                            oracle_reason=(
                                oracle_result["reason"]
                            ),
                            duration_seconds=round(
                                step_duration,
                                4,
                            ),
                            timestamp=datetime.now(
                                timezone.utc
                            ).isoformat(),
                        )
                    )

                    if not oracle_result["passed"]:
                        errors.append(
                            oracle_result["reason"]
                        )
                        status = "failed"
                        break

                except Exception as exception:
                    failed_actions += 1
                    status = "failed"

                    errors.append(
                        f"Step {step_number} failed: "
                        f"{type(exception).__name__}: "
                        f"{exception}"
                    )
                    break

        completed_at = datetime.now(
            timezone.utc
        )

        duration_seconds = round(
            time.perf_counter() - overall_start,
            4,
        )

        graph_summary = self.graph.summary()

        oracle_pass_rate = (
            successful_actions / actions_executed
            if actions_executed > 0
            else 0.0
        )

        result = ExperimentResult(
            experiment_name=experiment_name,
            sut_name=self.sut_name,
            start_url=self.start_url,
            started_at=started_at.isoformat(),
            completed_at=completed_at.isoformat(),
            duration_seconds=duration_seconds,
            status=status,
            actions_inferred=actions_inferred,
            actions_executed=actions_executed,
            successful_actions=successful_actions,
            failed_actions=failed_actions,
            states_discovered=graph_summary[
                "node_count"
            ],
            transitions_created=graph_summary[
                "edge_count"
            ],
            oracle_pass_rate=round(
                oracle_pass_rate,
                4,
            ),
            steps=[
                asdict(step)
                for step in steps
            ],
            errors=errors,
        )

        result_dictionary = asdict(result)

        self._save_outputs(
            experiment_name=experiment_name,
            result=result_dictionary,
        )

        return result_dictionary

    def _wait_for_angular(
        self,
        browser: BrowserManager,
    ) -> None:
        """
        Wait until the Angular application has rendered.
        """

        WebDriverWait(
            browser.driver,
            self.wait_timeout,
        ).until(
            lambda driver: driver.execute_script(
                """
                const root =
                    document.querySelector('app-root');

                return Boolean(
                    root &&
                    root.children.length > 0 &&
                    root.innerHTML.trim().length > 20
                );
                """
            )
        )

    def _wait_for_route(
        self,
        browser: BrowserManager,
        expected_route: str,
    ) -> None:
        """
        Wait until the browser reaches the expected route.
        """

        WebDriverWait(
            browser.driver,
            self.wait_timeout,
        ).until(
            lambda driver:
            expected_route in driver.current_url
        )

    @staticmethod
    def _select_route_action(
        actions: List[Dict[str, Any]],
        target_route: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Select a candidate link action matching the requested route.
        """

        normalized_route = (
            target_route.rstrip("/") or "/"
        )

        for action in actions:
            if action["action_type"] != "click":
                continue

            metadata = action.get(
                "metadata",
                {}
            )

            raw_href = (
                metadata.get("raw_href") or ""
            ).rstrip("/")

            href = (
                metadata.get("href") or ""
            ).rstrip("/")

            if raw_href == normalized_route:
                return action

            if href.endswith(normalized_route):
                return action

        return None

    @staticmethod
    def _route_text(
        target_route: str,
    ) -> str:
        """
        Convert a route into expected visible page text.
        """

        route_name = target_route.strip(
            "/"
        )

        if not route_name:
            return "ARES"

        return route_name.replace(
            "-",
            " ",
        ).title()

    def _save_outputs(
        self,
        experiment_name: str,
        result: Dict[str, Any],
    ) -> None:
        """
        Save experiment and state-graph JSON outputs.
        """

        safe_name = experiment_name.lower().replace(
            " ",
            "_",
        )

        result_path = (
            self.output_directory
            / f"{safe_name}_result.json"
        )

        graph_path = (
            self.output_directory
            / f"{safe_name}_state_graph.json"
        )

        with result_path.open(
            "w",
            encoding="utf-8",
        ) as output_file:
            json.dump(
                result,
                output_file,
                indent=2,
                ensure_ascii=False,
            )

        self.graph.save_json(
            graph_path
        )