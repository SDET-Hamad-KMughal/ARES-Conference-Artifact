"""Hybrid visual-DOM mapping utilities for ARES."""

from __future__ import annotations

from typing import Any, Iterable

from selenium.webdriver.remote.webdriver import WebDriver

from web_environment.dom_extractor import DOMExtractor


class VisualDOMMapper:
    """Map visual detections to DOM elements using viewport coordinates."""

    def __init__(self, driver: WebDriver) -> None:
        self.driver = driver
        self.dom_extractor = DOMExtractor(driver)

    def map_detection(self, detection: dict[str, Any]) -> dict[str, Any]:
        """
        Map one visual detection to the DOM element at its center point.

        Expected detection format:

        {
            "class_name": "button",
            "confidence": 0.95,
            "bbox": [x1, y1, x2, y2]
        }
        """
        normalized = self._normalize_detection(detection)

        center_x = normalized["center_x"]
        center_y = normalized["center_y"]

        dom_element = self.dom_extractor.get_element_at_point(
            center_x,
            center_y,
        )

        return {
            **normalized,
            "dom_element": dom_element,
            "mapped": dom_element is not None,
        }

    def map_detections(
        self,
        detections: Iterable[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Map multiple visual detections to DOM elements."""
        return [self.map_detection(detection) for detection in detections]

    def build_action_candidates(
        self,
        detections: Iterable[dict[str, Any]],
        require_dom_mapping: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Build unified action candidates from visual and DOM information.
        """
        mapped_detections = self.map_detections(detections)
        candidates: list[dict[str, Any]] = []

        for item in mapped_detections:
            dom_element = item["dom_element"]

            if require_dom_mapping and dom_element is None:
                continue

            candidate = {
                "visual_class": item["class_name"],
                "confidence": item["confidence"],
                "bbox": item["bbox"],
                "center_x": item["center_x"],
                "center_y": item["center_y"],
                "mapped": item["mapped"],
                "tag": "",
                "text": "",
                "id": "",
                "name": "",
                "type": "",
                "role": "",
                "class_name": "",
                "href": "",
                "placeholder": "",
                "aria_label": "",
                "x": None,
                "y": None,
                "width": None,
                "height": None,
                "enabled": None,
            }

            if dom_element is not None:
                candidate.update(dom_element)

            candidate["action_type"] = self._infer_action_type(candidate)
            candidates.append(candidate)

        return candidates

    @staticmethod
    def _normalize_detection(
        detection: dict[str, Any],
    ) -> dict[str, Any]:
        """Validate and normalize a visual detection."""

        if "bbox" not in detection:
            raise ValueError("Detection must contain a 'bbox' field.")

        bbox = detection["bbox"]

        if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
            raise ValueError(
                "Detection 'bbox' must contain [x1, y1, x2, y2]."
            )

        try:
            x1, y1, x2, y2 = [float(value) for value in bbox]
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Detection bounding-box coordinates must be numeric."
            ) from exc

        if x2 <= x1 or y2 <= y1:
            raise ValueError(
                "Detection bounding box must have positive width and height."
            )

        class_name = str(
            detection.get(
                "class_name",
                detection.get("class", detection.get("label", "unknown")),
            )
        )

        confidence = float(detection.get("confidence", 0.0))

        return {
            "class_name": class_name,
            "confidence": confidence,
            "bbox": [x1, y1, x2, y2],
            "center_x": (x1 + x2) / 2,
            "center_y": (y1 + y2) / 2,
        }

    @staticmethod
    def _infer_action_type(candidate: dict[str, Any]) -> str:
        """Infer the likely browser action for a mapped candidate."""

        tag = str(candidate.get("tag", "")).lower()
        input_type = str(candidate.get("type", "")).lower()
        role = str(candidate.get("role", "")).lower()
        visual_class = str(candidate.get("visual_class", "")).lower()

        if tag == "select":
            return "select"

        if tag == "textarea":
            return "type"

        if tag == "input":
            if input_type in {
                "text",
                "email",
                "password",
                "search",
                "tel",
                "url",
                "number",
                "date",
            }:
                return "type"

            if input_type in {
                "submit",
                "button",
                "checkbox",
                "radio",
                "file",
            }:
                return "click"

        if tag in {"a", "button", "option"}:
            return "click"

        if role in {"button", "link", "checkbox", "radio"}:
            return "click"

        if any(
            token in visual_class
            for token in (
                "button",
                "link",
                "checkbox",
                "radio",
                "icon",
            )
        ):
            return "click"

        if any(
            token in visual_class
            for token in (
                "input",
                "textbox",
                "text_field",
                "search",
            )
        ):
            return "type"

        return "inspect"