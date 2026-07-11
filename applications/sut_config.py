"""System-under-test configuration utilities for ARES."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SUTConfig:
    """Configuration for one web application under test."""

    name: str
    start_url: str
    goal_url_contains: str
    description: str = ""
    max_actions: int = 20
    max_steps: int = 50
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("SUT name cannot be empty.")

        if not self.start_url.strip():
            raise ValueError("SUT start URL cannot be empty.")

        if self.max_actions < 1:
            raise ValueError("max_actions must be at least 1.")

        if self.max_steps < 1:
            raise ValueError("max_steps must be at least 1.")

    def to_dict(self) -> dict[str, Any]:
        """Return the configuration as a dictionary."""

        return asdict(self)


class SUTRegistry:
    """Load and query configured systems under test."""

    def __init__(self, configurations: list[SUTConfig]) -> None:
        self._configurations = {
            configuration.name.lower(): configuration
            for configuration in configurations
        }

        if not self._configurations:
            raise ValueError(
                "At least one system-under-test configuration is required."
            )

    @classmethod
    def from_json(
        cls,
        path: str | Path,
    ) -> "SUTRegistry":
        """Load SUT configurations from a JSON file."""

        config_path = Path(path)

        if not config_path.exists():
            raise FileNotFoundError(
                f"SUT configuration file was not found: {config_path}"
            )

        payload = json.loads(
            config_path.read_text(encoding="utf-8")
        )

        if not isinstance(payload, list):
            raise ValueError(
                "SUT configuration JSON must contain a list."
            )

        configurations = [
            SUTConfig(
                name=str(item["name"]),
                start_url=str(item["start_url"]),
                goal_url_contains=str(
                    item.get("goal_url_contains", "")
                ),
                description=str(item.get("description", "")),
                max_actions=int(item.get("max_actions", 20)),
                max_steps=int(item.get("max_steps", 50)),
                enabled=bool(item.get("enabled", True)),
            )
            for item in payload
        ]

        return cls(configurations)

    def get(self, name: str) -> SUTConfig:
        """Return one configured system by name."""

        normalized_name = name.strip().lower()

        if normalized_name not in self._configurations:
            available = ", ".join(
                sorted(self._configurations)
            )

            raise KeyError(
                f"Unknown SUT: {name}. Available: {available}"
            )

        return self._configurations[normalized_name]

    def enabled(self) -> list[SUTConfig]:
        """Return all enabled systems."""

        return [
            configuration
            for configuration in self._configurations.values()
            if configuration.enabled
        ]

    def all(self) -> list[SUTConfig]:
        """Return every configured system."""

        return list(self._configurations.values())