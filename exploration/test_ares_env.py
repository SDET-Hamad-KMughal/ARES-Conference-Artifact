"""Smoke test for the ARES Gymnasium environment."""

from gymnasium.utils.env_checker import check_env

from exploration.ares_env import ARESEnvironment


def main() -> None:
    environment = ARESEnvironment(
        start_url="https://example.com",
        headless=False,
        max_actions=10,
        max_steps=5,
        goal_url_contains="iana.org",
    )

    try:
        check_env(environment, skip_render_check=True)

        observation, info = environment.reset(seed=42)

        print("Observation shape:", observation.shape)
        print("Initial information:", info)
        print("Action-space size:", environment.action_space.n)

        for step_number in range(5):
            action = environment.action_space.sample()

            observation, reward, terminated, truncated, info = (
                environment.step(action)
            )

            print(
                {
                    "step": step_number + 1,
                    "action": action,
                    "reward": reward,
                    "terminated": terminated,
                    "truncated": truncated,
                    "url": info["url"],
                    "result": info["action_result"],
                }
            )

            if terminated or truncated:
                break

        environment.render()

    finally:
        environment.close()


if __name__ == "__main__":
    main()