"""Train a Stable-Baselines3 PPO agent on the ARES environment."""

from __future__ import annotations

import argparse
from pathlib import Path

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.utils import set_random_seed

from exploration.ares_env import ARESEnvironment


def parse_arguments() -> argparse.Namespace:
    """Parse command-line training options."""

    parser = argparse.ArgumentParser(
        description="Train PPO on the ARES browser exploration environment."
    )

    parser.add_argument(
        "--url",
        default="https://example.com",
        help="Starting URL for browser exploration.",
    )

    parser.add_argument(
        "--goal",
        default="iana.org",
        help="Substring identifying a successful goal URL.",
    )

    parser.add_argument(
        "--timesteps",
        type=int,
        default=1_000,
        help="Total PPO training timesteps.",
    )

    parser.add_argument(
        "--max-actions",
        type=int,
        default=10,
        help="Maximum mapped action candidates.",
    )

    parser.add_argument(
        "--max-steps",
        type=int,
        default=10,
        help="Maximum actions in one episode.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed.",
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run Chrome without displaying the browser window.",
    )

    parser.add_argument(
        "--output",
        default="exploration/models/ares_ppo",
        help="Path used to save the final PPO model.",
    )

    return parser.parse_args()


def create_environment(
    start_url: str,
    goal_url_contains: str,
    headless: bool,
    max_actions: int,
    max_steps: int,
) -> Monitor:
    """Create and monitor one ARES training environment."""

    environment = ARESEnvironment(
        start_url=start_url,
        headless=headless,
        max_actions=max_actions,
        max_steps=max_steps,
        goal_url_contains=goal_url_contains,
    )

    return Monitor(environment)


def main() -> None:
    """Train and save the PPO exploration agent."""

    args = parse_arguments()

    if args.timesteps < 1:
        raise ValueError("--timesteps must be at least 1.")

    model_path = Path(args.output)
    model_path.parent.mkdir(parents=True, exist_ok=True)

    checkpoint_directory = Path("exploration/checkpoints")
    checkpoint_directory.mkdir(parents=True, exist_ok=True)

    log_directory = Path("results/ppo_training")
    log_directory.mkdir(parents=True, exist_ok=True)

    set_random_seed(args.seed)

    environment = create_environment(
        start_url=args.url,
        goal_url_contains=args.goal,
        headless=args.headless,
        max_actions=args.max_actions,
        max_steps=args.max_steps,
    )

    checkpoint_callback = CheckpointCallback(
        save_freq=250,
        save_path=str(checkpoint_directory),
        name_prefix="ares_ppo",
        save_replay_buffer=False,
        save_vecnormalize=False,
    )

    model = PPO(
        policy="MlpPolicy",
        env=environment,
        learning_rate=3e-4,
        n_steps=64,
        batch_size=32,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        vf_coef=0.5,
        max_grad_norm=0.5,
        seed=args.seed,
        verbose=1,
        tensorboard_log=str(log_directory),
        device="auto",
        policy_kwargs={
            "net_arch": {
                "pi": [128, 128],
                "vf": [128, 128],
            }
        },
    )

    try:
        print("Starting ARES PPO training.")
        print(f"Start URL: {args.url}")
        print(f"Goal URL token: {args.goal}")
        print(f"Training timesteps: {args.timesteps}")
        print(f"Observation size: {environment.observation_space.shape}")
        print(f"Action count: {environment.action_space.n}")

        model.learn(
            total_timesteps=args.timesteps,
            callback=checkpoint_callback,
            progress_bar=True,
        )

        model.save(str(model_path))

        print(f"PPO model saved to: {model_path}.zip")

    finally:
        environment.close()


if __name__ == "__main__":
    main()