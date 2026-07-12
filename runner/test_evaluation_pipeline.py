"""Smoke test for the ARES EvaluationPipeline."""

from pathlib import Path
from typing import Any, Dict

from runner.core.evaluation_pipeline import EvaluationPipeline


INPUT_PATH = Path(
    "runner/results/angular/experiment/"
    "angular_route_exploration_result.json"
)

OUTPUT_PATH = Path(
    "runner/results/angular/evaluation/"
    "angular_route_exploration_evaluation.json"
)


def print_evaluation(
    evaluation: Dict[str, Any],
) -> None:
    """
    Print evaluation metrics in a readable format.
    """

    execution = evaluation["execution"]
    actions = evaluation["actions"]
    graph = evaluation["graph"]
    oracle = evaluation["oracle"]
    quality = evaluation["quality"]

    print("=" * 70)
    print("ARES Evaluation Pipeline Smoke Test")
    print("=" * 70)

    print(
        f"Experiment: "
        f"{evaluation['experiment_name']}"
    )
    print(
        f"SUT: {evaluation['sut_name']}"
    )
    print(
        f"Status: {evaluation['status']}"
    )

    print("-" * 70)
    print("Execution Metrics")
    print("-" * 70)

    print(
        "Total duration: "
        f"{execution['total_duration_seconds']} seconds"
    )
    print(
        "Average action duration: "
        f"{execution['average_action_duration_seconds']} seconds"
    )
    print(
        "Minimum action duration: "
        f"{execution['minimum_action_duration_seconds']} seconds"
    )
    print(
        "Maximum action duration: "
        f"{execution['maximum_action_duration_seconds']} seconds"
    )

    print("-" * 70)
    print("Action Metrics")
    print("-" * 70)

    print(
        f"Actions inferred: "
        f"{actions['actions_inferred']}"
    )
    print(
        f"Actions executed: "
        f"{actions['actions_executed']}"
    )
    print(
        f"Successful actions: "
        f"{actions['successful_actions']}"
    )
    print(
        f"Failed actions: "
        f"{actions['failed_actions']}"
    )
    print(
        "Action success rate: "
        f"{actions['action_success_rate']:.2%}"
    )
    print(
        "Inferred execution ratio: "
        f"{actions['inferred_execution_ratio']:.2%}"
    )

    print("-" * 70)
    print("State Graph Metrics")
    print("-" * 70)

    print(
        f"States discovered: "
        f"{graph['states_discovered']}"
    )
    print(
        f"Transitions created: "
        f"{graph['transitions_created']}"
    )
    print(
        "Transition coverage: "
        f"{graph['transition_coverage']:.2%}"
    )
    print(
        "State transition ratio: "
        f"{graph['state_transition_ratio']:.4f}"
    )

    print("-" * 70)
    print("Oracle Metrics")
    print("-" * 70)

    print(
        "Oracle pass rate: "
        f"{oracle['oracle_pass_rate']:.2%}"
    )
    print(
        "Average oracle score: "
        f"{oracle['average_oracle_score']:.4f}"
    )

    print("-" * 70)
    print("Quality Checks")
    print("-" * 70)

    print(
        "Completed without failures: "
        f"{quality['completed_without_failures']}"
    )
    print(
        "All executed actions recorded: "
        f"{quality['all_executed_actions_recorded']}"
    )
    print(
        "All transitions recorded: "
        f"{quality['all_transitions_recorded']}"
    )

    print(
        f"Evaluation JSON saved: "
        f"{OUTPUT_PATH}"
    )

    print("=" * 70)


def main() -> None:
    """
    Load an experiment result and evaluate it.
    """

    pipeline = EvaluationPipeline()

    experiment_result = pipeline.load_json(
        INPUT_PATH
    )

    evaluation = pipeline.evaluate(
        experiment_result
    )

    saved_path = pipeline.save_json(
        evaluation,
        OUTPUT_PATH
    )

    print_evaluation(evaluation)

    assert saved_path.exists(), (
        f"Evaluation output was not created: "
        f"{saved_path}"
    )

    assert evaluation["status"] == "completed", (
        "Expected completed experiment status."
    )

    assert (
        evaluation["actions"][
            "actions_executed"
        ]
        == 4
    ), "Expected four executed actions."

    assert (
        evaluation["actions"][
            "successful_actions"
        ]
        == 4
    ), "Expected four successful actions."

    assert (
        evaluation["actions"][
            "failed_actions"
        ]
        == 0
    ), "Expected zero failed actions."

    assert (
        evaluation["actions"][
            "action_success_rate"
        ]
        == 1.0
    ), "Expected 100% action success rate."

    assert (
        evaluation["graph"][
            "states_discovered"
        ]
        == 5
    ), "Expected five discovered states."

    assert (
        evaluation["graph"][
            "transitions_created"
        ]
        == 4
    ), "Expected four transitions."

    assert (
        evaluation["graph"][
            "transition_coverage"
        ]
        == 1.0
    ), "Expected 100% transition coverage."

    assert (
        evaluation["oracle"][
            "oracle_pass_rate"
        ]
        == 1.0
    ), "Expected 100% oracle pass rate."

    assert (
        evaluation["quality"][
            "completed_without_failures"
        ]
        is True
    ), "Expected a failure-free experiment."

    assert (
        evaluation["quality"][
            "all_executed_actions_recorded"
        ]
        is True
    ), "Expected all actions to be recorded."

    assert (
        evaluation["quality"][
            "all_transitions_recorded"
        ]
        is True
    ), "Expected all transitions to be recorded."

    print("Evaluation pipeline test passed.")


if __name__ == "__main__":
    main()