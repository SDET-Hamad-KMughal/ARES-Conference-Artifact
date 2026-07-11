"""Run ARES experiments for one configured system under test."""

from __future__ import annotations

import argparse
from pathlib import Path

from applications.sut_config import SUTRegistry
from evaluation.run_experiments import (
    print_agent_summary,
    run_ppo_episode,
    run_random_episode,
    save_results,
)
from exploration.ares_env import ARESEnvironment
from stable_baselines3 import PPO


def parse_arguments() -> argparse.Namespace:
    """Parse command-line options."""

    parser = argparse.ArgumentParser(
        description="Run PPO and random experiments for one configured SUT."
    )

    parser.add_argument(
        "--sut",
        required=True,
        help="Configured system name from config/applications.json.",
    )

    parser.add_argument(
        "--config",
        default="config/applications.json",
        help="SUT registry JSON path.",
    )

    parser.add_argument(
        "--model",
        default="exploration/models/ares_ppo.zip",
        help="Saved PPO model path.",
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
        "--headless",
        action="store_true",
        help="Run Chrome without showing the browser.",
    )

    parser.add_argument(
        "--allow-disabled",
        action="store_true",
        help="Allow experiments for a disabled SUT configuration.",
    )

    return parser.parse_args()


def main() -> None:
    """Run matched PPO and random experiments for one SUT."""

    args = parse_arguments()

    if args.episodes < 1:
        raise ValueError("--episodes must be at least 1.")

    registry = SUTRegistry.from_json(args.config)
    sut = registry.get(args.sut)

    if not sut.enabled and not args.allow_disabled:
        raise RuntimeError(
            f"SUT '{sut.name}' is disabled in {args.config}. "
            "Verify its URL and goal, then enable it or use --allow-disabled."
        )

    model_path = Path(args.model)

    if not model_path.exists():
        raise FileNotFoundError(
            f"PPO model was not found: {model_path}"
        )

    output_path = Path(
        "results"
    ) / "evaluation" / sut.name / "agent_comparison.csv"

    environment = ARESEnvironment(
        start_url=sut.start_url,
        goal_url_contains=sut.goal_url_contains,
        headless=args.headless,
        max_actions=sut.max_actions,
        max_steps=sut.max_steps,
    )

    model = PPO.load(
        str(model_path),
        env=environment,
        device="auto",
    )

    results = []

    try:
        for episode in range(1, args.episodes + 1):
            seed = args.seed + episode - 1

            print(
                f"[{sut.name}] Random episode {episode}/{args.episodes}, "
                f"seed={seed}"
            )

            results.append(
                run_random_episode(
                    environment=environment,
                    episode=episode,
                    seed=seed,
                )
            )

            print(
                f"[{sut.name}] PPO episode {episode}/{args.episodes}, "
                f"seed={seed}"
            )

            results.append(
                run_ppo_episode(
                    model=model,
                    environment=environment,
                    episode=episode,
                    seed=seed,
                )
            )

    finally:
        environment.close()

    saved_path = save_results(
        results=results,
        output_path=output_path,
    )

    print_agent_summary("random", results)
    print_agent_summary("ppo", results)

    print()
    print(f"SUT: {sut.name}")
    print(f"Start URL: {sut.start_url}")
    print(f"Goal token: {sut.goal_url_contains}")
    print(f"Results saved to: {saved_path}")


if __name__ == "__main__":
    main()