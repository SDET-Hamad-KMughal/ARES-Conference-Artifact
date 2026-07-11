"""Aggregate ARES experiment results into paper-ready metrics."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


@dataclass
class AgentMetrics:
    """Aggregate measurements for one exploration agent."""

    agent: str
    episodes: int
    successful_episodes: int
    success_rate: float
    average_reward: float
    reward_std: float
    average_steps: float
    steps_std: float
    average_visited_states: float
    average_successful_actions: float
    average_failed_actions: float


def load_results(path: str | Path) -> list[dict[str, Any]]:
    """Load episode-level experiment results from CSV."""

    csv_path = Path(path)

    if not csv_path.exists():
        raise FileNotFoundError(f"Results file not found: {csv_path}")

    rows: list[dict[str, Any]] = []

    with csv_path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as csv_file:
        reader = csv.DictReader(csv_file)

        for row in reader:
            rows.append(
                {
                    "agent": row["agent"],
                    "episode": int(row["episode"]),
                    "seed": int(row["seed"]),
                    "total_reward": float(row["total_reward"]),
                    "steps": int(row["steps"]),
                    "goal_reached": (
                        row["goal_reached"].strip().lower() == "true"
                    ),
                    "final_url": row["final_url"],
                    "visited_states": int(row["visited_states"]),
                    "successful_actions": int(row["successful_actions"]),
                    "failed_actions": int(row["failed_actions"]),
                }
            )

    if not rows:
        raise ValueError("The experiment CSV contains no result rows.")

    return rows


def calculate_agent_metrics(
    rows: list[dict[str, Any]],
) -> list[AgentMetrics]:
    """Calculate aggregate statistics for every agent."""

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in rows:
        grouped[str(row["agent"])].append(row)

    metrics: list[AgentMetrics] = []

    for agent_name in sorted(grouped):
        agent_rows = grouped[agent_name]

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

        successful_actions = [
            int(row["successful_actions"])
            for row in agent_rows
        ]

        failed_actions = [
            int(row["failed_actions"])
            for row in agent_rows
        ]

        successful_episodes = sum(
            1
            for row in agent_rows
            if bool(row["goal_reached"])
        )

        metrics.append(
            AgentMetrics(
                agent=agent_name,
                episodes=len(agent_rows),
                successful_episodes=successful_episodes,
                success_rate=(
                    successful_episodes / len(agent_rows)
                ),
                average_reward=mean(rewards),
                reward_std=(
                    pstdev(rewards)
                    if len(rewards) > 1
                    else 0.0
                ),
                average_steps=mean(steps),
                steps_std=(
                    pstdev(steps)
                    if len(steps) > 1
                    else 0.0
                ),
                average_visited_states=mean(visited_states),
                average_successful_actions=mean(
                    successful_actions
                ),
                average_failed_actions=mean(
                    failed_actions
                ),
            )
        )

    return metrics


def save_summary_csv(
    metrics: list[AgentMetrics],
    output_path: str | Path,
) -> Path:
    """Save aggregate metrics as CSV."""

    if not metrics:
        raise ValueError("No metrics were provided.")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(asdict(metrics[0]).keys())

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for metric in metrics:
            writer.writerow(asdict(metric))

    return path


def save_summary_json(
    metrics: list[AgentMetrics],
    output_path: str | Path,
) -> Path:
    """Save aggregate metrics as JSON."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = [
        asdict(metric)
        for metric in metrics
    ]

    path.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    return path


def print_markdown_table(
    metrics: list[AgentMetrics],
) -> None:
    """Print a compact table suitable for paper drafting."""

    print()
    print(
        "| Agent | Episodes | Success Rate | "
        "Reward (Mean ± SD) | Steps (Mean ± SD) | "
        "Visited States |"
    )
    print(
        "|---|---:|---:|---:|---:|---:|"
    )

    for metric in metrics:
        print(
            f"| {metric.agent.upper()} "
            f"| {metric.episodes} "
            f"| {metric.success_rate:.2%} "
            f"| {metric.average_reward:.2f} ± "
            f"{metric.reward_std:.2f} "
            f"| {metric.average_steps:.2f} ± "
            f"{metric.steps_std:.2f} "
            f"| {metric.average_visited_states:.2f} |"
        )


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Aggregate ARES experiment metrics."
    )

    parser.add_argument(
        "--input",
        default="results/evaluation/agent_comparison.csv",
        help="Episode-level comparison CSV.",
    )

    parser.add_argument(
        "--csv-output",
        default="results/evaluation/agent_summary.csv",
        help="Aggregate CSV output.",
    )

    parser.add_argument(
        "--json-output",
        default="results/evaluation/agent_summary.json",
        help="Aggregate JSON output.",
    )

    return parser.parse_args()


def main() -> None:
    """Aggregate and print experiment results."""

    args = parse_arguments()

    rows = load_results(args.input)
    metrics = calculate_agent_metrics(rows)

    csv_path = save_summary_csv(
        metrics,
        args.csv_output,
    )

    json_path = save_summary_json(
        metrics,
        args.json_output,
    )

    print_markdown_table(metrics)

    print()
    print(f"Summary CSV saved to: {csv_path}")
    print(f"Summary JSON saved to: {json_path}")


if __name__ == "__main__":
    main()