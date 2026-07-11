"""Evaluate a trained PPO model on the ARES environment."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
from stable_baselines3 import PPO

from exploration.ares_env import ARESEnvironment


def parse_arguments() -> argparse.Namespace:
    """Parse evaluation arguments."""

    parser = argparse.ArgumentParser(
        description="Evaluate a trained ARES PPO model."
    )

    parser.add_argument(
        "--model",
        default="exploration/models/ares_ppo.zip",
        help="Path to the saved PPO model.",
    )

    parser.add_argument(
        "--url",
        default="https://example.com",
        help="Starting URL.",
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
        help="Number of evaluation episodes.",
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
        "--headless",
        action="store_true",
        help="Run Chrome in headless mode.",
    )

    return parser.parse_args()


def run_episode(
    model: PPO,
    environment: ARESEnvironment,
    episode_number: int,
) -> dict[str, Any]:
    """Run one deterministic evaluation episode."""

    observation, initial_info = environment.reset(
        seed=episode_number
    )

    total_reward = 0.0
    steps = 0
    goal_reached = False
    final_url = initial_info["url"]

    while True:
        action, _state = model.predict(
            observation,
            deterministic=True,
        )

        action_value = int(np.asarray(action).item())

        observation, reward, terminated, truncated, info = (
            environment.step(action_value)
        )

        total_reward += float(reward)
        steps += 1
        final_url = info["url"]
        goal_reached = bool(info["goal_reached"])

        print(
            {
                "episode": episode_number,
                "step": steps,
                "action": action_value,
                "reward": reward,
                "url": final_url,
                "goal_reached": goal_reached,
                "action_result": info["action_result"],
            }
        )

        if terminated or truncated:
            break

    return {
        "episode": episode_number,
        "reward": total_reward,
        "steps": steps,
        "goal_reached": goal_reached,
        "final_url": final_url,
    }


def main() -> None:
    """Load and evaluate the PPO model."""

    args = parse_arguments()

    model_path = Path(args.model)

    if not model_path.exists():
        raise FileNotFoundError(
            f"PPO model does not exist: {model_path}"
        )

    if args.episodes < 1:
        raise ValueError("--episodes must be at least 1.")

    environment = ARESEnvironment(
        start_url=args.url,
        headless=args.headless,
        max_actions=args.max_actions,
        max_steps=args.max_steps,
        goal_url_contains=args.goal,
    )

    model = PPO.load(
        str(model_path),
        env=environment,
        device="auto",
    )

    results: list[dict[str, Any]] = []

    try:
        for episode_number in range(1, args.episodes + 1):
            result = run_episode(
                model=model,
                environment=environment,
                episode_number=episode_number,
            )

            results.append(result)

    finally:
        environment.close()

    successful_episodes = sum(
        1 for result in results if result["goal_reached"]
    )

    average_reward = sum(
        float(result["reward"]) for result in results
    ) / len(results)

    average_steps = sum(
        int(result["steps"]) for result in results
    ) / len(results)

    print("\nEvaluation summary")
    print("------------------")
    print(f"Episodes: {len(results)}")
    print(f"Successful episodes: {successful_episodes}")
    print(
        "Success rate: "
        f"{successful_episodes / len(results):.2%}"
    )
    print(f"Average reward: {average_reward:.2f}")
    print(f"Average steps: {average_steps:.2f}")


if __name__ == "__main__":
    main()