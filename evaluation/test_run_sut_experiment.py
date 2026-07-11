"""Smoke test for configured SUT experiment support."""

from applications.sut_config import SUTRegistry


def main() -> None:
    registry = SUTRegistry.from_json(
        "config/applications.json"
    )

    sut = registry.get("example-domain")

    assert sut.enabled is True
    assert sut.start_url == "https://example.com"
    assert sut.goal_url_contains == "iana.org"
    assert sut.max_actions == 10
    assert sut.max_steps == 10

    print("Configured SUT experiment test passed.")


if __name__ == "__main__":
    main()