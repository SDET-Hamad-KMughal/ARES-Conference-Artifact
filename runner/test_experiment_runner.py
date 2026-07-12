"""Smoke test for the ARES ExperimentRunner."""

from pathlib import Path
from typing import Any, Dict

from runner.core.experiment_runner import ExperimentRunner


OUTPUT_DIRECTORY = Path(
    "runner/results/angular/experiment"
)

START_URL = "http://localhost:4200/login"

ROUTE_SEQUENCE = [
    "/catalog",
    "/cart",
    "/checkout",
    "/success",
]


def print_result(
    result: Dict[str, Any],
) -> None:
    """
    Print the complete experiment summary.
    """

    print("=" * 70)
    print("ARES Experiment Runner Smoke Test")
    print("=" * 70)
    print(
        f"Experiment: "
        f"{result['experiment_name']}"
    )
    print(
        f"SUT: {result['sut_name']}"
    )
    print(
        f"Status: {result['status']}"
    )
    print(
        f"Start URL: {result['start_url']}"
    )
    print(
        f"Duration: "
        f"{result['duration_seconds']} seconds"
    )
    print(
        f"Actions inferred: "
        f"{result['actions_inferred']}"
    )
    print(
        f"Actions executed: "
        f"{result['actions_executed']}"
    )
    print(
        f"Successful actions: "
        f"{result['successful_actions']}"
    )
    print(
        f"Failed actions: "
        f"{result['failed_actions']}"
    )
    print(
        f"States discovered: "
        f"{result['states_discovered']}"
    )
    print(
        f"Transitions created: "
        f"{result['transitions_created']}"
    )
    print(
        f"Oracle pass rate: "
        f"{result['oracle_pass_rate']:.2%}"
    )

    print("-" * 70)
    print("Steps")
    print("-" * 70)

    for step in result["steps"]:
        print(
            f"Step {step['step_number']}: "
            f"{step['action_label']}"
        )
        print(
            f"  {step['source_url']}"
        )
        print(
            f"  -> {step['target_url']}"
        )
        print(
            f"  Oracle: "
            f"{'PASS' if step['oracle_passed'] else 'FAIL'}"
        )
        print(
            f"  Score: "
            f"{step['oracle_score']}"
        )
        print(
            f"  Duration: "
            f"{step['duration_seconds']} seconds"
        )

    if result["errors"]:
        print("-" * 70)
        print("Errors")

        for error in result["errors"]:
            print(f"- {error}")

    print("=" * 70)


def main() -> None:
    """
    Run the end-to-end Angular route experiment.
    """

    runner = ExperimentRunner(
        sut_name="angular",
        start_url=START_URL,
        output_directory=OUTPUT_DIRECTORY,
        headless=False,
    )

    result = runner.run_route_experiment(
        experiment_name=(
            "Angular Route Exploration"
        ),
        route_sequence=ROUTE_SEQUENCE,
    )

    print_result(result)

    assert result["status"] == "completed", (
        f"Experiment failed: {result['errors']}"
    )

    assert result["actions_executed"] == 4, (
        "Expected four executed actions."
    )

    assert result["successful_actions"] == 4, (
        "Expected four successful actions."
    )

    assert result["failed_actions"] == 0, (
        "Expected zero failed actions."
    )

    assert result["states_discovered"] == 5, (
        "Expected five discovered states."
    )

    assert result["transitions_created"] == 4, (
        "Expected four state transitions."
    )

    assert result["oracle_pass_rate"] == 1.0, (
        "Expected a 100% oracle pass rate."
    )

    print("Experiment runner test passed.")


if __name__ == "__main__":
    main()