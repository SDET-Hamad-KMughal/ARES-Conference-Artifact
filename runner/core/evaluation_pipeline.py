"""ARES evaluation pipeline.

Reads experiment output and produces conference-ready evaluation metrics.
"""

import json
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List


class EvaluationPipeline:
    """
    Compute aggregate metrics from an ARES experiment result.
    """

    def evaluate(
        self,
        experiment_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Compute evaluation metrics from one experiment result.
        """

        steps: List[Dict[str, Any]] = experiment_result.get(
            "steps",
            [],
        )

        durations = [
            float(step.get("duration_seconds", 0.0))
            for step in steps
        ]

        oracle_scores = [
            float(step.get("oracle_score", 0.0))
            for step in steps
        ]

        executed_actions = int(
            experiment_result.get(
                "actions_executed",
                0,
            )
        )

        successful_actions = int(
            experiment_result.get(
                "successful_actions",
                0,
            )
        )

        failed_actions = int(
            experiment_result.get(
                "failed_actions",
                0,
            )
        )

        states_discovered = int(
            experiment_result.get(
                "states_discovered",
                0,
            )
        )

        transitions_created = int(
            experiment_result.get(
                "transitions_created",
                0,
            )
        )

        actions_inferred = int(
            experiment_result.get(
                "actions_inferred",
                0,
            )
        )

        action_success_rate = (
            successful_actions / executed_actions
            if executed_actions > 0
            else 0.0
        )

        transition_coverage = (
            transitions_created / executed_actions
            if executed_actions > 0
            else 0.0
        )

        state_transition_ratio = (
            transitions_created / states_discovered
            if states_discovered > 0
            else 0.0
        )

        inferred_execution_ratio = (
            executed_actions / actions_inferred
            if actions_inferred > 0
            else 0.0
        )

        average_action_duration = (
            mean(durations)
            if durations
            else 0.0
        )

        average_oracle_score = (
            mean(oracle_scores)
            if oracle_scores
            else 0.0
        )

        return {
            "experiment_name": experiment_result.get(
                "experiment_name"
            ),
            "sut_name": experiment_result.get(
                "sut_name"
            ),
            "status": experiment_result.get(
                "status"
            ),
            "execution": {
                "total_duration_seconds": float(
                    experiment_result.get(
                        "duration_seconds",
                        0.0,
                    )
                ),
                "average_action_duration_seconds": round(
                    average_action_duration,
                    4,
                ),
                "minimum_action_duration_seconds": round(
                    min(durations) if durations else 0.0,
                    4,
                ),
                "maximum_action_duration_seconds": round(
                    max(durations) if durations else 0.0,
                    4,
                ),
            },
            "actions": {
                "actions_inferred": actions_inferred,
                "actions_executed": executed_actions,
                "successful_actions": successful_actions,
                "failed_actions": failed_actions,
                "action_success_rate": round(
                    action_success_rate,
                    4,
                ),
                "inferred_execution_ratio": round(
                    inferred_execution_ratio,
                    4,
                ),
            },
            "graph": {
                "states_discovered": states_discovered,
                "transitions_created": transitions_created,
                "transition_coverage": round(
                    transition_coverage,
                    4,
                ),
                "state_transition_ratio": round(
                    state_transition_ratio,
                    4,
                ),
            },
            "oracle": {
                "oracle_pass_rate": float(
                    experiment_result.get(
                        "oracle_pass_rate",
                        0.0,
                    )
                ),
                "average_oracle_score": round(
                    average_oracle_score,
                    4,
                ),
            },
            "quality": {
                "completed_without_failures": (
                    experiment_result.get("status")
                    == "completed"
                    and failed_actions == 0
                ),
                "all_executed_actions_recorded": (
                    len(steps) == executed_actions
                ),
                "all_transitions_recorded": (
                    transitions_created
                    == executed_actions
                ),
            },
            "errors": experiment_result.get(
                "errors",
                [],
            ),
        }

    @staticmethod
    def load_json(
        input_path: str | Path,
    ) -> Dict[str, Any]:
        """
        Load an experiment result JSON file.
        """

        path = Path(input_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Experiment result not found: {path}"
            )

        with path.open(
            "r",
            encoding="utf-8",
        ) as input_file:
            return json.load(input_file)

    @staticmethod
    def save_json(
        evaluation: Dict[str, Any],
        output_path: str | Path,
    ) -> Path:
        """
        Save evaluation metrics as formatted JSON.
        """

        path = Path(output_path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with path.open(
            "w",
            encoding="utf-8",
        ) as output_file:
            json.dump(
                evaluation,
                output_file,
                indent=2,
                ensure_ascii=False,
            )

        return path