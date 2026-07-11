"""Random exploration baseline for the ARES framework."""

from __future__ import annotations

import argparse
import csv
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from exploration.ares_env import ARESEnvironment


@dataclass
class RandomEpisodeResult:
    """Measurements collected from one random exploration episode."""

    episode: int
    seed: int
    total_reward: float
    steps: int
    goal_reached: bool
    final_url: str
    visited_states: int
    successful_actions: int
    failed_actions: int


class RandomCrawler:
    """Explore a web application by selecting random valid actions."""

    def __init__(
        self,
        start_url: str,
        goal_url_contains: str | None = None,
        headless: bool = False,
        max_actions: int = 10,
        max_steps: int = 10,
    ) -> None:
        self.environment = ARESEnvironment(
            start_url=start_url,
            goal_url_contains=goal_url_contains,
            headless=headless,
            max_actions=max_actions,
            max_steps=max_steps,
        )

    def run_episode(
        self,
        episode_number: int,
        seed: int,
    ) -> RandomEpisodeResult:
        """Run one random exploration episode."""

        random.seed(seed)
        np.random.seed(seed)
        self.environment.action_space.seed(seed)

        _observation, initial_info = self.environment.reset(seed=seed)

        total_reward = 0.0
        steps = 0
        goal_reached = False
        final_url = initial_info["url"]
        visited_states = initial_info["visited_states"]
        successful_actions = 0
        failed_actions = 0

        while True:
            action = int(self.environment.action_space.sample())

            (
                _observation,
                reward,
                terminated,
                truncated,
                info,
            ) = self.environment.step(action)

            steps += 1
            total_reward += float(reward)
            final_url = info["url"]
            visited_states = info["visited_states"]
            goal_reached = bool(info["goal_reached"])

            if info["action_result"] == "success":
                successful_actions += 1
            else:
                failed_actions += 1

            print(
                {
                    "episode": episode_number,
                    "step": steps,
                    "action": action,
                    "reward": reward,
                    "url": final_url,
                    "new_state": info["new_state"],
                    "goal_reached": goal_reached,
                    "result": info["action_result"],
                }
            )

            if terminated or truncated:
                break

        return RandomEpisodeResult(
            episode=episode_number,
            seed=seed,
            total_reward=total_reward,
            steps=steps,
            goal_reached=goal_reached,
            final_url=final_url,
            visited_states=visited_states,
            successful_actions=successful_actions,
            failed_actions=failed_actions,
        )

    def run(
        self,
        episodes: int,
        base_seed: int = 42,
    ) -> list[RandomEpisodeResult]:
        """Run multiple random baseline episodes."""

        if episodes < 1:
            raise ValueError("episodes must be at least 1.")

        results: list[RandomEpisodeResult] = []

        for episode_number in range(1, episodes + 1):
            seed = base_seed + episode_number - 1

            result = self.run_episode(
                episode_number=episode_number,
                seed=seed,
            )

            results.append(result)

        return results

    def close(self) -> None:
        """Close the browser environment."""

        self.environment.close()


def save_results(
    results: list[RandomEpisodeResult],
    output_path: str | Path,
) -> Path:
    """Save random baseline measurements as CSV."""

    if not results:
        raise ValueError("No random baseline results were provided.")

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


def print_summary(
    results: list[RandomEpisodeResult],
) -> None:
    """Print aggregate random baseline measurements."""

    if not results:
        raise ValueError("No results available for summary.")

    successful_episodes = sum(
        1 for result in results if result.goal_reached
    )

    average_reward = sum(
        result.total_reward for result in results
    ) / len(results)

    average_steps = sum(
        result.steps for result in results
    ) / len(results)

    average_states = sum(
        result.visited_states for result in results
    ) / len(results)

    total_successful_actions = sum(
        result.successful_actions for result in results
    )

    total_failed_actions = sum(
        result.failed_actions for result in results
    )

    print("\nRandom baseline summary")
    print("-----------------------")
    print(f"Episodes: {len(results)}")
    print(f"Successful episodes: {successful_episodes}")
    print(
        "Success rate: "
        f"{successful_episodes / len(results):.2%}"
    )
    print(f"Average reward: {average_reward:.2f}")
    print(f"Average steps: {average_steps:.2f}")
    print(f"Average visited states: {average_states:.2f}")
    print(f"Successful actions: {total_successful_actions}")
    print(f"Failed actions: {total_failed_actions}")


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Run the ARES random exploration baseline."
    )

    parser.add_argument(
        "--url",
        default="https://example.com",
        help="Starting web application URL.",
    )

    parser.add_argument(
        "--goal",
        default="iana.org",
        help="Substring identifying a successful goal URL.",
    )

    parser.add_argument(
        "--episodes",
        type=int,
        default=3,
        help="Number of random exploration episodes.",
    )

    parser.add_argument(
        "--max-actions",
        type=int,
        default=10,
        help="Maximum mapped candidate actions.",
    )

    parser.add_argument(
        "--max-steps",
        type=int,
        default=10,
        help="Maximum steps per episode.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Base random seed.",
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run Chrome without displaying its window.",
    )

    parser.add_argument(
        "--output",
        default="results/random_baseline/random_results.csv",
        help="CSV output path.",
    )

    return parser.parse_args()


def main() -> None:
    """Run the random baseline from the command line."""

    args = parse_arguments()

    crawler = RandomCrawler(
        start_url=args.url,
        goal_url_contains=args.goal,
        headless=args.headless,
        max_actions=args.max_actions,
        max_steps=args.max_steps,
    )

    try:
        results = crawler.run(
            episodes=args.episodes,
            base_seed=args.seed,
        )
    finally:
        crawler.close()

    output_path = save_results(
        results=results,
        output_path=args.output,
    )

    print_summary(results)
    print(f"Results saved to: {output_path}")


if __name__ == "__main__":
    main()