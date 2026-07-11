"""Aggregate ARES exploration and self-healing evaluation results."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean
from typing import Any


def load_csv(path: str | Path) -> list[dict[str, str]]:
    """Load a CSV file into a list of dictionaries."""

    csv_path = Path(path)

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with csv_path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as csv_file:
        return list(csv.DictReader(csv_file))


def parse_bool(value: str) -> bool:
    """Convert a CSV boolean value to bool."""

    return value.strip().lower() == "true"


def aggregate_agent_results(
    rows: list[dict[str, str]],
) -> dict[str, Any]:
    """Aggregate PPO and random exploration measurements."""

    grouped: dict[str, list[dict[str, str]]] = {}

    for row in rows:
        grouped.setdefault(row["agent"], []).append(row)

    summary: dict[str, Any] = {}

    for agent, agent_rows in grouped.items():
        rewards = [
            float(row["total_reward"])
            for row in agent_rows
        ]

        steps = [
            int(row["steps"])
            for row in agent_rows
        ]

        visited_states = [
            int(row["visited_states"])
            for row in agent_rows
        ]

        successful_episodes = sum(
            1
            for row in agent_rows
            if parse_bool(row["goal_reached"])
        )

        summary[agent] = {
            "episodes": len(agent_rows),
            "successful_episodes": successful_episodes,
            "success_rate": (
                successful_episodes / len(agent_rows)
            ),
            "average_reward": mean(rewards),
            "average_steps": mean(steps),
            "average_visited_states": mean(visited_states),
        }

    return summary


def aggregate_healing_results(
    rows: list[dict[str, str]],
) -> dict[str, Any]:
    """Aggregate self-healing fault-injection measurements."""

    healed_faults = sum(
        1 for row in rows if parse_bool(row["healed"])
    )

    executed_replacements = sum(
        1
        for row in rows
        if parse_bool(row["replacement_executed"])
    )

    selected_scores = [
        float(row["selected_score"])
        for row in rows
    ]

    return {
        "injected_faults": len(rows),
        "healed_faults": healed_faults,
        "healing_success_rate": healed_faults / len(rows),
        "executed_replacements": executed_replacements,
        "average_selected_score": mean(selected_scores),
        "faults": rows,
    }


def save_json(
    payload: dict[str, Any],
    output_path: str | Path,
) -> Path:
    """Save aggregate results as JSON."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    return path


def save_markdown(
    payload: dict[str, Any],
    output_path: str | Path,
) -> Path:
    """Save a paper-ready Markdown summary."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    agent_results = payload["exploration"]
    healing_results = payload["self_healing"]

    lines = [
        "# ARES Evaluation Summary",
        "",
        "## Exploration Comparison",
        "",
        "| Agent | Episodes | Success Rate | Average Reward | Average Steps | Average Visited States |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    for agent_name in sorted(agent_results):
        result = agent_results[agent_name]

        lines.append(
            f"| {agent_name.upper()} "
            f"| {result['episodes']} "
            f"| {result['success_rate']:.2%} "
            f"| {result['average_reward']:.2f} "
            f"| {result['average_steps']:.2f} "
            f"| {result['average_visited_states']:.2f} |"
        )

    lines.extend(
        [
            "",
            "## Self-Healing Fault Injection",
            "",
            f"- Injected faults: {healing_results['injected_faults']}",
            f"- Healed faults: {healing_results['healed_faults']}",
            (
                "- Healing success rate: "
                f"{healing_results['healing_success_rate']:.2%}"
            ),
            (
                "- Executed replacements: "
                f"{healing_results['executed_replacements']}"
            ),
            (
                "- Average selected score: "
                f"{healing_results['average_selected_score']:.4f}"
            ),
            "",
            "## Interpretation",
            "",
            (
                "These results validate the integration of the ARES browser, "
                "exploration, self-healing, and script-generation components "
                "on controlled smoke-test and synthetic fault-injection scenarios."
            ),
            "",
            (
                "They should not be treated as evidence for the full conference "
                "evaluation until the experiments are repeated on all selected "
                "systems under test, with the planned seeds, fault sets, and metrics."
            ),
            "",
        ]
    )

    path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    return path


def parse_arguments() -> argparse.Namespace:
    """Parse command-line options."""

    parser = argparse.ArgumentParser(
        description="Aggregate all current ARES evaluation outputs."
    )

    parser.add_argument(
        "--agent-results",
        default="results/evaluation/agent_comparison.csv",
    )

    parser.add_argument(
        "--healing-results",
        default="results/evaluation/fault_injection_results.csv",
    )

    parser.add_argument(
        "--json-output",
        default="results/evaluation/aggregate_results.json",
    )

    parser.add_argument(
        "--markdown-output",
        default="results/evaluation/evaluation_summary.md",
    )

    return parser.parse_args()


def main() -> None:
    """Aggregate exploration and healing results."""

    args = parse_arguments()

    agent_rows = load_csv(args.agent_results)
    healing_rows = load_csv(args.healing_results)

    payload = {
        "exploration": aggregate_agent_results(agent_rows),
        "self_healing": aggregate_healing_results(healing_rows),
        "scope": {
            "status": "integration_validation",
            "paper_ready": False,
        },
    }

    json_path = save_json(
        payload,
        args.json_output,
    )

    markdown_path = save_markdown(
        payload,
        args.markdown_output,
    )

    print(json.dumps(payload, indent=2))
    print()
    print(f"Aggregate JSON saved to: {json_path}")
    print(f"Markdown summary saved to: {markdown_path}")


if __name__ == "__main__":
    main()