"""Run comparable PPO and random-baseline ARES experiments."""

from __future__ import annotations

import argparse
import csv
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
from stable_baselines3 import PPO

from exploration.ares_env import ARESEnvironment


@dataclass
class ExperimentResult:
    """Measurements from one exploration episode."""

    agent: str
    episode: int
    seed: int
    total_reward: float
    steps: int
    goal_reached: bool
    final_url: str
    visited_states: int
    successful_actions: int
    failed_actions: int


def run_random_episode(
    environment: ARESEnvironment,
    episode: int,
    seed: int,
) -> ExperimentResult:
    """Run one random-agent episode."""

    random.seed(seed)
    np.random.seed(seed)
    environment.action_space.seed(seed)

    _observation, initial_info = environment.reset(seed=seed)

    total_reward = 0.0
    steps = 0
    goal_reached = False
    final_url = initial_info["url"]
    visited_states = initial_info["visited_states"]
    successful_actions = 0
    failed_actions = 0

    while True:
        action = int(environment.action_space.sample())

        (
            _observation,
            reward,
            terminated,
            truncated,
            info,
        ) = environment.step(action)

        total_reward += float(reward)
        steps += 1
        goal_reached = bool(info["goal_reached"])
        final_url = info["url"]
        visited_states = int(info["visited_states"])

        if info["action_result"] == "success":
            successful_actions += 1
        else:
            failed_actions += 1

        if terminated or truncated:
            break

    return ExperimentResult(
        agent="random",
        episode=episode,
        seed=seed,
        total_reward=total_reward,
        steps=steps,
        goal_reached=goal_reached,
        final_url=final_url,
        visited_states=visited_states,
        successful_actions=successful_actions,
        failed_actions=failed_actions,
    )


def run_ppo_episode(
    model: PPO,
    environment: ARESEnvironment,
    episode: int,
    seed: int,
) -> ExperimentResult:
    """Run one deterministic PPO episode."""

    observation, initial_info = environment.reset(seed=seed)

    total_reward = 0.0
    steps = 0
    goal_reached = False
    final_url = initial_info["url"]
    visited_states = initial_info["visited_states"]
    successful_actions = 0
    failed_actions = 0

    while True:
        action, _state = model.predict(
            observation,
            deterministic=True,
        )

        action_value = int(np.asarray(action).item())

        (
            observation,
            reward,
            terminated,
            truncated,
            info,
        ) = environment.step(action_value)

        total_reward += float(reward)
        steps += 1
        goal_reached = bool(info["goal_reached"])
        final_url = info["url"]
        visited_states = int(info["visited_states"])

        if info["action_result"] == "success":
            successful_actions += 1
        else:
            failed_actions += 1

        if terminated or truncated:
            break

    return ExperimentResult(
        agent="ppo",
        episode=episode,
        seed=seed,
        total_reward=total_reward,
        steps=steps,
        goal_reached=goal_reached,
        final_url=final_url,
        visited_states=visited_states,
        successful_actions=successful_actions,
        failed_actions=failed_actions,
    )


def save_results(
    results: list[ExperimentResult],
    output_path: str | Path,
) -> Path:
    """Save all episode measurements to CSV."""

    if not results:
        raise ValueError("No experiment results were provided.")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(asdict(results[0]).keys())

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for result in results:
            writer.writerow(asdict(result))

    return path


def print_agent_summary(
    agent_name: str,
    results: list[ExperimentResult],
) -> None:
    """Print aggregate results for one agent."""

    agent_results = [
        result
        for result in results
        if result.agent == agent_name
    ]

    if not agent_results:
        return

    successes = sum(
        1 for result in agent_results if result.goal_reached
    )

    average_reward = sum(
        result.total_reward for result in agent_results
    ) / len(agent_results)

    average_steps = sum(
        result.steps for result in agent_results
    ) / len(agent_results)

    average_states = sum(
        result.visited_states for result in agent_results
    ) / len(agent_results)

    print(f"\n{agent_name.upper()} summary")
    print("-" * (len(agent_name) + 8))
    print(f"Episodes: {len(agent_results)}")
    print(f"Successful episodes: {successes}")
    print(
        f"Success rate: "
        f"{successes / len(agent_results):.2%}"
    )
    print(f"Average reward: {average_reward:.2f}")
    print(f"Average steps: {average_steps:.2f}")
    print(f"Average visited states: {average_states:.2f}")


def parse_arguments() -> argparse.Namespace:
    """Parse experiment arguments."""

    parser = argparse.ArgumentParser(
        description="Compare PPO and random ARES exploration."
    )

    parser.add_argument(
        "--model",
        default="exploration/models/ares_ppo.zip",
        help="Saved PPO model path.",
    )

    parser.add_argument(
        "--url",
        default="https://example.com",
        help="Starting application URL.",
    )

    parser.add_argument(
        "--goal",
        default="iana.org",
        help="Goal URL substring.",
    )

    parser.add_argument(
        "--episodes",
        type=int,
        default=5,
        help="Episodes per agent.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Base random seed.",
    )

    parser.add_argument(
        "--max-actions",
        type=int,
        default=10,
        help="Maximum mapped actions.",
    )

    parser.add_argument(
        "--max-steps",
        type=int,
        default=10,
        help="Maximum episode steps.",
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run Chrome in headless mode.",
    )

    parser.add_argument(
        "--output",
        default="results/evaluation/agent_comparison.csv",
        help="Combined experiment CSV.",
    )

    return parser.parse_args()


def main() -> None:
    """Run identical-seed PPO and random experiments."""

    args = parse_arguments()

    if args.episodes < 1:
        raise ValueError("--episodes must be at least 1.")

    model_path = Path(args.model)

    if not model_path.exists():
        raise FileNotFoundError(
            f"PPO model was not found: {model_path}"
        )

    environment = ARESEnvironment(
        start_url=args.url,
        goal_url_contains=args.goal,
        headless=args.headless,
        max_actions=args.max_actions,
        max_steps=args.max_steps,
    )

    model = PPO.load(
        str(model_path),
        env=environment,
        device="auto",
    )

    results: list[ExperimentResult] = []

    try:
        for episode in range(1, args.episodes + 1):
            seed = args.seed + episode - 1

            print(
                f"Running random episode {episode} "
                f"with seed {seed}"
            )

            random_result = run_random_episode(
                environment=environment,
                episode=episode,
                seed=seed,
            )

            results.append(random_result)

            print(
                f"Running PPO episode {episode} "
                f"with seed {seed}"
            )

            ppo_result = run_ppo_episode(
                model=model,
                environment=environment,
                episode=episode,
                seed=seed,
            )

            results.append(ppo_result)

    finally:
        environment.close()

    output_path = save_results(
        results=results,
        output_path=args.output,
    )

    print_agent_summary("random", results)
    print_agent_summary("ppo", results)

    print(f"\nCombined results saved to: {output_path}")


if __name__ == "__main__":
    main()