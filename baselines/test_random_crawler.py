"""Smoke test for the ARES random exploration baseline."""

from pathlib import Path

from baselines.random_crawler import RandomCrawler, save_results


def main() -> None:
    crawler = RandomCrawler(
        start_url="https://example.com",
        goal_url_contains="iana.org",
        headless=True,
        max_actions=10,
        max_steps=5,
    )

    try:
        results = crawler.run(
            episodes=1,
            base_seed=42,
        )
    finally:
        crawler.close()

    assert len(results) == 1

    result = results[0]

    assert result.steps >= 1
    assert result.steps <= 5

    output_path = save_results(
        results,
        "results/random_baseline/test_random_results.csv",
    )

    assert Path(output_path).exists()

    print(result)
    print("Random crawler test passed.")


if __name__ == "__main__":
    main()