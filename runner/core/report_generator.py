"""ARES conference artifact report generator.

Converts evaluation metrics into a concise, human-readable research report.
"""

from pathlib import Path
from typing import Any, Dict


class ReportGenerator:
    """
    Generate a text report from EvaluationPipeline output.
    """

    @staticmethod
    def generate(
        evaluation: Dict[str, Any],
    ) -> str:
        """
        Build a formatted conference artifact report.
        """

        execution = evaluation["execution"]
        actions = evaluation["actions"]
        graph = evaluation["graph"]
        oracle = evaluation["oracle"]
        quality = evaluation["quality"]

        overall_result = (
            "PASS"
            if quality["completed_without_failures"]
            else "FAIL"
        )

        lines = [
            "=" * 72,
            "ARES CONFERENCE ARTIFACT EVALUATION REPORT",
            "=" * 72,
            "",
            "Experiment",
            "-" * 72,
            f"Name: {evaluation['experiment_name']}",
            f"SUT: {evaluation['sut_name']}",
            f"Status: {evaluation['status']}",
            "",
            "Execution Metrics",
            "-" * 72,
            (
                "Total duration: "
                f"{execution['total_duration_seconds']:.4f} seconds"
            ),
            (
                "Average action duration: "
                f"{execution['average_action_duration_seconds']:.4f} seconds"
            ),
            (
                "Minimum action duration: "
                f"{execution['minimum_action_duration_seconds']:.4f} seconds"
            ),
            (
                "Maximum action duration: "
                f"{execution['maximum_action_duration_seconds']:.4f} seconds"
            ),
            "",
            "Action Metrics",
            "-" * 72,
            f"Actions inferred: {actions['actions_inferred']}",
            f"Actions executed: {actions['actions_executed']}",
            f"Successful actions: {actions['successful_actions']}",
            f"Failed actions: {actions['failed_actions']}",
            (
                "Action success rate: "
                f"{actions['action_success_rate']:.2%}"
            ),
            (
                "Inferred execution ratio: "
                f"{actions['inferred_execution_ratio']:.2%}"
            ),
            "",
            "State Graph Metrics",
            "-" * 72,
            f"States discovered: {graph['states_discovered']}",
            f"Transitions created: {graph['transitions_created']}",
            (
                "Transition coverage: "
                f"{graph['transition_coverage']:.2%}"
            ),
            (
                "State-transition ratio: "
                f"{graph['state_transition_ratio']:.4f}"
            ),
            "",
            "Oracle Metrics",
            "-" * 72,
            (
                "Oracle pass rate: "
                f"{oracle['oracle_pass_rate']:.2%}"
            ),
            (
                "Average oracle score: "
                f"{oracle['average_oracle_score']:.4f}"
            ),
            "",
            "Quality Checks",
            "-" * 72,
            (
                "Completed without failures: "
                f"{quality['completed_without_failures']}"
            ),
            (
                "All executed actions recorded: "
                f"{quality['all_executed_actions_recorded']}"
            ),
            (
                "All transitions recorded: "
                f"{quality['all_transitions_recorded']}"
            ),
            "",
            "Overall Result",
            "-" * 72,
            overall_result,
            "",
            "=" * 72,
        ]

        return "\n".join(lines)

    @staticmethod
    def save(
        report: str,
        output_path: str | Path,
    ) -> Path:
        """
        Save the generated report to a text file.
        """

        path = Path(output_path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            report,
            encoding="utf-8",
        )

        return path