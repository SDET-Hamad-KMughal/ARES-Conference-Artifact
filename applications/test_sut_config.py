"""Smoke test for the ARES SUT configuration registry."""

from applications.sut_config import SUTRegistry


def main() -> None:
    registry = SUTRegistry.from_json(
        "config/applications.json"
    )

    example = registry.get("example-domain")

    assert example.start_url == "https://example.com"
    assert example.goal_url_contains == "iana.org"
    assert example.enabled is True

    enabled_systems = registry.enabled()

    assert len(enabled_systems) == 1
    assert enabled_systems[0].name == "example-domain"

    print("Configured systems:")

    for configuration in registry.all():
        print(configuration.to_dict())

    print("SUT configuration test passed.")


if __name__ == "__main__":
    main()