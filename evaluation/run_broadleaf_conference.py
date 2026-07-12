"""Run the implementation-centric ARES evaluation on Broadleaf."""

import json
from pathlib import Path
from typing import Any, Dict

from runner.core.experiment_runner import ExperimentRunner


OUTPUT_DIRECTORY = Path("results/broadleaf")


def save_json(
    path: Path,
    data: Dict[str, Any],
) -> None:
    """Save formatted JSON data."""

    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def save_text_report(
    path: Path,
    result: Dict[str, Any],
) -> None:
    """Save a human-readable experiment report."""

    workflow_completed = (
        "Yes"
        if result.get("status") == "completed"
        else "No"
    )

    report_lines = [
        "ARES Broadleaf Conference Evaluation",
        "=" * 44,
        "",
        f"Experiment: {result.get('experiment_name')}",
        f"SUT: {result.get('sut_name')}",
        f"Start URL: {result.get('start_url')}",
        f"Status: {result.get('status')}",
        f"Workflow Completed: {workflow_completed}",
        "",
        "Measured Results",
        "-" * 44,
        f"Actions Inferred: {result.get('actions_inferred', 0)}",
        f"Actions Executed: {result.get('actions_executed', 0)}",
        f"Successful Actions: {result.get('successful_actions', 0)}",
        f"Failed Actions: {result.get('failed_actions', 0)}",
        f"States Discovered: {result.get('states_discovered', 0)}",
        f"State Transitions: {result.get('transitions_created', 0)}",
        (
            "Oracle Pass Rate: "
            f"{result.get('oracle_pass_rate', 0.0) * 100:.2f}%"
        ),
        (
            "Workflow Execution Time: "
            f"{result.get('duration_seconds', 0.0):.4f} seconds"
        ),
        "Report Generated: Yes",
        "",
        "Execution Errors",
        "-" * 44,
    ]

    errors = result.get("errors", [])

    if errors:
        for index, error in enumerate(
            errors,
            start=1,
        ):
            report_lines.append(
                f"{index}. {error}"
            )
    else:
        report_lines.append("None")

    report_lines.extend(
        [
            "",
            "Executed Steps",
            "-" * 44,
        ]
    )

    steps = result.get("steps", [])

    if not steps:
        report_lines.append(
            "No successful execution steps were recorded."
        )
    else:
        for step in steps:
            report_lines.extend(
                [
                    (
                        f"Step {step.get('step_number')}: "
                        f"{step.get('action_label')}"
                    ),
                    (
                        "  Action type: "
                        f"{step.get('action_type')}"
                    ),
                    (
                        "  Source URL: "
                        f"{step.get('source_url')}"
                    ),
                    (
                        "  Target URL: "
                        f"{step.get('target_url')}"
                    ),
                    (
                        "  Oracle passed: "
                        f"{step.get('oracle_passed')}"
                    ),
                    (
                        "  Oracle score: "
                        f"{step.get('oracle_score')}"
                    ),
                    (
                        "  Oracle reason: "
                        f"{step.get('oracle_reason')}"
                    ),
                    (
                        "  Duration: "
                        f"{step.get('duration_seconds')} seconds"
                    ),
                    "",
                ]
            )

    path.write_text(
        "\n".join(report_lines),
        encoding="utf-8",
    )


def main() -> None:
    """Execute Broadleaf and generate evaluation artifacts."""

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    runner = ExperimentRunner(
        sut_name="Broadleaf",
        start_url="https://localhost:8443",
        output_directory=OUTPUT_DIRECTORY,
        headless=False,
        wait_timeout=30,
    )

    route_sequence = [
        "/hot-sauces",
        "/hot-sauces/hoppin_hot_sauce",
        "/merchandise",
        "/about_us",
    ]

    result = runner.run_route_experiment(
        experiment_name="broadleaf_conference_evaluation",
        route_sequence=route_sequence,
    )

    summary = {
        "sut": result.get("sut_name"),
        "workflow_completed": (
            result.get("status") == "completed"
        ),
        "status": result.get("status"),
        "actions_inferred": result.get(
            "actions_inferred",
            0,
        ),
        "actions_executed": result.get(
            "actions_executed",
            0,
        ),
        "successful_actions": result.get(
            "successful_actions",
            0,
        ),
        "failed_actions": result.get(
            "failed_actions",
            0,
        ),
        "states_discovered": result.get(
            "states_discovered",
            0,
        ),
        "state_transitions": result.get(
            "transitions_created",
            0,
        ),
        "oracle_pass_rate": result.get(
            "oracle_pass_rate",
            0.0,
        ),
        "execution_time_seconds": result.get(
            "duration_seconds",
            0.0,
        ),
        "report_generated": True,
        "errors": result.get(
            "errors",
            [],
        ),
    }

    raw_result_path = (
        OUTPUT_DIRECTORY
        / "broadleaf_raw_result.json"
    )

    summary_path = (
        OUTPUT_DIRECTORY
        / "broadleaf_evaluation_summary.json"
    )

    text_report_path = (
        OUTPUT_DIRECTORY
        / "broadleaf_conference_report.txt"
    )

    save_json(
        raw_result_path,
        result,
    )

    save_json(
        summary_path,
        summary,
    )

    save_text_report(
        text_report_path,
        result,
    )

    print()
    print("=" * 60)
    print("ARES Broadleaf Conference Evaluation")
    print("=" * 60)
    print(
        "Workflow completed: "
        f"{summary['workflow_completed']}"
    )
    print(
        f"Status: {summary['status']}"
    )
    print(
        "Actions inferred: "
        f"{summary['actions_inferred']}"
    )
    print(
        "Actions executed: "
        f"{summary['actions_executed']}"
    )
    print(
        "Successful actions: "
        f"{summary['successful_actions']}"
    )
    print(
        "Failed actions: "
        f"{summary['failed_actions']}"
    )
    print(
        "States discovered: "
        f"{summary['states_discovered']}"
    )
    print(
        "State transitions: "
        f"{summary['state_transitions']}"
    )
    print(
        "Oracle pass rate: "
        f"{summary['oracle_pass_rate'] * 100:.2f}%"
    )
    print(
        "Execution time: "
        f"{summary['execution_time_seconds']:.4f} seconds"
    )
    print()
    print(
        f"Raw result: {raw_result_path}"
    )
    print(
        f"Summary: {summary_path}"
    )
    print(
        f"Text report: {text_report_path}"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()