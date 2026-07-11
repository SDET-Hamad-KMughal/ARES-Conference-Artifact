"""Gymnasium environment for ARES browser exploration."""

from __future__ import annotations

import hashlib
from typing import Any, Optional

import gymnasium as gym
import numpy as np
from gymnasium import spaces
from selenium.common.exceptions import WebDriverException

from web_environment.browser_env import BrowserEnvironment
from web_environment.visual_dom_mapper import VisualDOMMapper


class ARESEnvironment(gym.Env):
    """
    PPO-compatible environment for autonomous web exploration.

    The environment obtains interactive browser elements, represents them as
    fixed-size numerical observations, executes browser actions, and rewards
    the discovery of previously unseen browser states.
    """

    metadata = {"render_modes": ["human"]}

    ACTION_CLICK = 0
    ACTION_TYPE = 1
    ACTION_SELECT = 2
    ACTION_SCROLL = 3
    ACTION_BACK = 4
    ACTION_REFRESH = 5
    ACTION_NOOP = 6

    def __init__(
        self,
        start_url: str,
        headless: bool = False,
        max_actions: int = 20,
        max_steps: int = 50,
        timeout: int = 15,
        goal_url_contains: Optional[str] = None,
    ) -> None:
        super().__init__()

        if max_actions < 1:
            raise ValueError("max_actions must be at least 1.")

        if max_steps < 1:
            raise ValueError("max_steps must be at least 1.")

        self.start_url = start_url
        self.headless = headless
        self.max_actions = max_actions
        self.max_steps = max_steps
        self.timeout = timeout
        self.goal_url_contains = goal_url_contains

        self.browser = BrowserEnvironment(
            headless=headless,
            timeout=timeout,
        )

        self.mapper: Optional[VisualDOMMapper] = None
        self.current_candidates: list[dict[str, Any]] = []

        self.current_step = 0
        self.visited_states: set[str] = set()
        self.action_history: list[dict[str, Any]] = []

        # One action selects one candidate. Extra actions are navigation actions.
        self.scroll_down_action = max_actions
        self.scroll_up_action = max_actions + 1
        self.back_action = max_actions + 2
        self.refresh_action = max_actions + 3

        self.action_space = spaces.Discrete(max_actions + 4)

        # Each candidate contributes eight normalized features.
        self.features_per_candidate = 8

        # Additional global state:
        # URL hash, progress, candidate count, history count.
        self.global_feature_count = 4

        observation_size = (
            max_actions * self.features_per_candidate
            + self.global_feature_count
        )

        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(observation_size,),
            dtype=np.float32,
        )

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[dict[str, Any]] = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        """Reset the browser and return the initial PPO observation."""

        super().reset(seed=seed)

        self.browser.close()
        self.browser.start()
        self.browser.open(self.start_url)

        driver = self.browser.driver

        if driver is None:
            raise RuntimeError("Browser driver was not initialized.")

        self.mapper = VisualDOMMapper(driver)

        self.current_step = 0
        self.visited_states.clear()
        self.action_history.clear()

        self.current_candidates = self._collect_action_candidates()

        state_signature = self._state_signature()
        self.visited_states.add(state_signature)

        observation = self._build_observation()

        info = {
            "url": self.browser.current_url(),
            "candidate_count": len(self.current_candidates),
            "visited_states": len(self.visited_states),
        }

        return observation, info

    def step(
        self,
        action: int,
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        """Execute one browser action and return the environment transition."""

        if not self.action_space.contains(action):
            raise ValueError(f"Invalid action: {action}")

        self.current_step += 1

        previous_url = self.browser.current_url()
        previous_signature = self._state_signature()

        reward = 0.0
        action_result = "success"
        executed_action: dict[str, Any] = {
            "step": self.current_step,
            "action": int(action),
        }

        try:
            if action < self.max_actions:
                reward += self._execute_candidate_action(action, executed_action)

            elif action == self.scroll_down_action:
                self.browser.scroll_by(y=600)
                executed_action["type"] = "scroll_down"

            elif action == self.scroll_up_action:
                self.browser.scroll_by(y=-600)
                executed_action["type"] = "scroll_up"

            elif action == self.back_action:
                self.browser.back()
                executed_action["type"] = "back"

            elif action == self.refresh_action:
                self.browser.refresh()
                executed_action["type"] = "refresh"

        except (RuntimeError, WebDriverException, IndexError) as exc:
            reward -= 2.0
            action_result = "failed"
            executed_action["error"] = str(exc)

        self.action_history.append(executed_action)

        self.current_candidates = self._collect_action_candidates()

        current_url = self.browser.current_url()
        current_signature = self._state_signature()

        new_state = current_signature not in self.visited_states
        url_changed = current_url != previous_url
        dom_changed = current_signature != previous_signature

        if url_changed:
            reward += 5.0

        if new_state:
            reward += 2.0
            self.visited_states.add(current_signature)
        elif dom_changed:
            reward += 0.5
        else:
            reward -= 0.5

        goal_reached = self._goal_reached(current_url)

        if goal_reached:
            reward += 10.0

        terminated = goal_reached
        truncated = self.current_step >= self.max_steps

        observation = self._build_observation()

        info = {
            "url": current_url,
            "previous_url": previous_url,
            "action_result": action_result,
            "candidate_count": len(self.current_candidates),
            "visited_states": len(self.visited_states),
            "new_state": new_state,
            "url_changed": url_changed,
            "goal_reached": goal_reached,
            "executed_action": executed_action,
        }

        return observation, float(reward), terminated, truncated, info

    def _collect_action_candidates(self) -> list[dict[str, Any]]:
        """
        Collect hybrid action candidates.

        This prototype converts extracted DOM geometry into simulated visual
        detections. Actual YOLO detections will later replace this provider.
        """

        if self.mapper is None:
            raise RuntimeError("Environment must be reset before collecting actions.")

        interactive_elements = (
            self.mapper.dom_extractor.extract_interactive_elements()
        )

        detections: list[dict[str, Any]] = []

        for element in interactive_elements:
            width = float(element.get("width", 0.0))
            height = float(element.get("height", 0.0))

            if width <= 0 or height <= 0:
                continue

            x = float(element.get("x", 0.0))
            y = float(element.get("y", 0.0))

            detections.append(
                {
                    "class_name": self._visual_class_for_element(element),
                    "confidence": 1.0,
                    "bbox": [
                        x,
                        y,
                        x + width,
                        y + height,
                    ],
                }
            )

        candidates = self.mapper.build_action_candidates(
            detections,
            require_dom_mapping=True,
        )

        return candidates[: self.max_actions]

    def _execute_candidate_action(
        self,
        action_index: int,
        action_record: dict[str, Any],
    ) -> float:
        """Execute the selected mapped candidate."""

        if action_index >= len(self.current_candidates):
            action_record["type"] = "invalid_candidate"
            return -1.0

        candidate = self.current_candidates[action_index]
        action_type = candidate.get("action_type", "inspect")

        action_record.update(
            {
                "type": action_type,
                "candidate_index": action_index,
                "tag": candidate.get("tag", ""),
                "text": candidate.get("text", ""),
            }
        )

        if action_type == "click":
            self._click_candidate(candidate)
            return 0.5

        if action_type == "type":
            self._type_candidate(candidate)
            return 0.25

        if action_type == "select":
            action_record["note"] = "Selection requires task-specific options."
            return -0.25

        action_record["note"] = "Candidate was inspected but not executed."
        return -0.25

    def _click_candidate(self, candidate: dict[str, Any]) -> None:
        """Click the center coordinates of a visual-DOM candidate."""

        center_x = int(float(candidate["center_x"]))
        center_y = int(float(candidate["center_y"]))

        driver = self.browser._require_driver()

        clicked = driver.execute_script(
            """
            const element = document.elementFromPoint(
                arguments[0],
                arguments[1]
            );

            if (!element) {
                return false;
            }

            element.click();
            return true;
            """,
            center_x,
            center_y,
        )

        if not clicked:
            raise RuntimeError(
                f"No clickable element found at ({center_x}, {center_y})."
            )

    def _type_candidate(self, candidate: dict[str, Any]) -> None:
        """Enter deterministic prototype text into an input candidate."""

        center_x = int(float(candidate["center_x"]))
        center_y = int(float(candidate["center_y"]))

        driver = self.browser._require_driver()

        typed = driver.execute_script(
            """
            const element = document.elementFromPoint(
                arguments[0],
                arguments[1]
            );

            if (!element) {
                return false;
            }

            element.focus();
            element.value = 'ARES test input';
            element.dispatchEvent(
                new Event('input', {bubbles: true})
            );
            element.dispatchEvent(
                new Event('change', {bubbles: true})
            );

            return true;
            """,
            center_x,
            center_y,
        )

        if not typed:
            raise RuntimeError(
                f"No input element found at ({center_x}, {center_y})."
            )

    def _build_observation(self) -> np.ndarray:
        """Convert current browser candidates into a fixed-length vector."""

        features: list[float] = []

        driver = self.browser._require_driver()

        viewport_width = max(
            float(driver.execute_script("return window.innerWidth;")),
            1.0,
        )
        viewport_height = max(
            float(driver.execute_script("return window.innerHeight;")),
            1.0,
        )

        for index in range(self.max_actions):
            if index < len(self.current_candidates):
                candidate = self.current_candidates[index]

                features.extend(
                    [
                        self._normalize_coordinate(
                            candidate.get("center_x", 0.0),
                            viewport_width,
                        ),
                        self._normalize_coordinate(
                            candidate.get("center_y", 0.0),
                            viewport_height,
                        ),
                        self._normalize_coordinate(
                            candidate.get("width", 0.0),
                            viewport_width,
                        ),
                        self._normalize_coordinate(
                            candidate.get("height", 0.0),
                            viewport_height,
                        ),
                        self._clip(candidate.get("confidence", 0.0)),
                        1.0 if candidate.get("enabled") else 0.0,
                        self._encode_action_type(
                            candidate.get("action_type", "inspect")
                        ),
                        self._encode_tag(candidate.get("tag", "")),
                    ]
                )
            else:
                features.extend([0.0] * self.features_per_candidate)

        features.extend(
            [
                self._stable_hash(self.browser.current_url()),
                min(self.current_step / self.max_steps, 1.0),
                min(
                    len(self.current_candidates) / self.max_actions,
                    1.0,
                ),
                min(len(self.action_history) / self.max_steps, 1.0),
            ]
        )

        observation = np.asarray(features, dtype=np.float32)

        if observation.shape != self.observation_space.shape:
            raise RuntimeError(
                "Generated observation has an unexpected shape: "
                f"{observation.shape}"
            )

        return observation

    def _state_signature(self) -> str:
        """Build a deterministic signature for the current browser state."""

        candidate_summary = [
            (
                candidate.get("tag", ""),
                candidate.get("text", ""),
                candidate.get("id", ""),
                candidate.get("action_type", ""),
            )
            for candidate in self.current_candidates
        ]

        raw_state = repr(
            (
                self.browser.current_url(),
                self.browser.page_title(),
                candidate_summary,
            )
        )

        return hashlib.sha256(raw_state.encode("utf-8")).hexdigest()

    def _goal_reached(self, current_url: str) -> bool:
        """Return whether the configured exploration goal was reached."""

        if not self.goal_url_contains:
            return False

        return self.goal_url_contains.lower() in current_url.lower()

    @staticmethod
    def _visual_class_for_element(element: dict[str, Any]) -> str:
        """Create a visual class label from DOM metadata."""

        tag = str(element.get("tag", "")).lower()
        input_type = str(element.get("type", "")).lower()

        if tag == "input" and input_type:
            return f"input_{input_type}"

        if tag:
            return tag

        return "unknown"

    @staticmethod
    def _normalize_coordinate(value: Any, maximum: float) -> float:
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return 0.0

        return float(np.clip(numeric_value / maximum, 0.0, 1.0))

    @staticmethod
    def _clip(value: Any) -> float:
        try:
            return float(np.clip(float(value), 0.0, 1.0))
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _stable_hash(value: str) -> float:
        digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
        integer_value = int(digest[:8], 16)

        return integer_value / 0xFFFFFFFF

    @staticmethod
    def _encode_action_type(action_type: str) -> float:
        mapping = {
            "inspect": 0.0,
            "click": 0.25,
            "type": 0.5,
            "select": 0.75,
        }

        return mapping.get(str(action_type).lower(), 0.0)

    @staticmethod
    def _encode_tag(tag: str) -> float:
        mapping = {
            "a": 0.1,
            "button": 0.2,
            "input": 0.3,
            "textarea": 0.4,
            "select": 0.5,
            "option": 0.6,
        }

        return mapping.get(str(tag).lower(), 0.0)

    def render(self) -> None:
        """Print a compact representation of the current browser state."""

        print(
            {
                "url": self.browser.current_url(),
                "step": self.current_step,
                "candidates": len(self.current_candidates),
                "visited_states": len(self.visited_states),
            }
        )

    def close(self) -> None:
        """Release the browser used by the environment."""

        self.browser.close()
        self.mapper = None