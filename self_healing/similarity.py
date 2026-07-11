"""Similarity functions used by the ARES self-healing engine."""

from __future__ import annotations

import math
from difflib import SequenceMatcher
from typing import Any, Optional

import numpy as np
from sentence_transformers import SentenceTransformer


class SimilarityEngine:
    """Calculate semantic, structural, and spatial locator similarity."""

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> None:
        self.model_name = model_name
        self._model: Optional[SentenceTransformer] = None

    @property
    def model(self) -> SentenceTransformer:
        """Load the Sentence-BERT model only when first required."""

        if self._model is None:
            self._model = SentenceTransformer(self.model_name)

        return self._model

    def semantic_similarity(
        self,
        original: dict[str, Any],
        candidate: dict[str, Any],
    ) -> float:
        """
        Calculate Sentence-BERT similarity between two DOM elements.

        Text is constructed from visible text and semantic attributes.
        """

        original_text = self._build_semantic_text(original)
        candidate_text = self._build_semantic_text(candidate)

        if not original_text or not candidate_text:
            return 0.0

        embeddings = self.model.encode(
            [original_text, candidate_text],
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        similarity = float(np.dot(embeddings[0], embeddings[1]))

        # Cosine similarity may theoretically fall between -1 and 1.
        # ARES uses a normalized score between 0 and 1.
        return self._clip((similarity + 1.0) / 2.0)

    def structural_similarity(
        self,
        original: dict[str, Any],
        candidate: dict[str, Any],
    ) -> float:
        """
        Compare DOM structure and locator-related attributes.

        The score combines:
        - tag similarity
        - element type similarity
        - role similarity
        - parent-path similarity
        - attribute similarity
        """

        component_scores: list[float] = []

        component_scores.append(
            self._exact_match(
                original.get("tag"),
                candidate.get("tag"),
            )
        )

        component_scores.append(
            self._exact_match(
                original.get("type"),
                candidate.get("type"),
            )
        )

        component_scores.append(
            self._exact_match(
                original.get("role"),
                candidate.get("role"),
            )
        )

        component_scores.append(
            self._path_similarity(
                original.get("xpath", ""),
                candidate.get("xpath", ""),
            )
        )

        component_scores.append(
            self._attribute_similarity(original, candidate)
        )

        return self._clip(sum(component_scores) / len(component_scores))

    def spatial_similarity(
        self,
        original: dict[str, Any],
        candidate: dict[str, Any],
        viewport_width: float,
        viewport_height: float,
    ) -> float:
        """
        Compare element positions using normalized Euclidean distance.

        A score of 1 means identical center coordinates.
        A score near 0 means the elements are far apart.
        """

        if viewport_width <= 0 or viewport_height <= 0:
            raise ValueError(
                "Viewport width and height must be positive."
            )

        original_center = self._element_center(original)
        candidate_center = self._element_center(candidate)

        original_x = original_center[0] / viewport_width
        original_y = original_center[1] / viewport_height

        candidate_x = candidate_center[0] / viewport_width
        candidate_y = candidate_center[1] / viewport_height

        distance = math.sqrt(
            (original_x - candidate_x) ** 2
            + (original_y - candidate_y) ** 2
        )

        maximum_distance = math.sqrt(2.0)

        similarity = 1.0 - (distance / maximum_distance)

        return self._clip(similarity)

    def calculate_components(
        self,
        original: dict[str, Any],
        candidate: dict[str, Any],
        viewport_width: float,
        viewport_height: float,
    ) -> dict[str, float]:
        """Return all three similarity scores."""

        return {
            "semantic": self.semantic_similarity(
                original,
                candidate,
            ),
            "structural": self.structural_similarity(
                original,
                candidate,
            ),
            "spatial": self.spatial_similarity(
                original,
                candidate,
                viewport_width,
                viewport_height,
            ),
        }

    @staticmethod
    def _build_semantic_text(element: dict[str, Any]) -> str:
        """Construct semantic text from DOM metadata."""

        values = [
            element.get("text", ""),
            element.get("aria_label", ""),
            element.get("placeholder", ""),
            element.get("name", ""),
            element.get("id", ""),
            element.get("title", ""),
            element.get("value", ""),
        ]

        normalized_values = [
            str(value).strip()
            for value in values
            if value is not None and str(value).strip()
        ]

        return " ".join(normalized_values)

    @staticmethod
    def _attribute_similarity(
        original: dict[str, Any],
        candidate: dict[str, Any],
    ) -> float:
        """Compare important locator-related attributes."""

        attribute_names = [
            "id",
            "name",
            "class_name",
            "placeholder",
            "aria_label",
            "href",
        ]

        scores: list[float] = []

        for attribute_name in attribute_names:
            original_value = str(
                original.get(attribute_name, "")
            ).strip().lower()

            candidate_value = str(
                candidate.get(attribute_name, "")
            ).strip().lower()

            if not original_value and not candidate_value:
                continue

            if not original_value or not candidate_value:
                scores.append(0.0)
                continue

            scores.append(
                SequenceMatcher(
                    None,
                    original_value,
                    candidate_value,
                ).ratio()
            )

        if not scores:
            return 0.0

        return sum(scores) / len(scores)

    @staticmethod
    def _path_similarity(
        original_path: Any,
        candidate_path: Any,
    ) -> float:
        """Compare two XPath strings."""

        original_value = str(original_path).strip().lower()
        candidate_value = str(candidate_path).strip().lower()

        if not original_value and not candidate_value:
            return 1.0

        if not original_value or not candidate_value:
            return 0.0

        return SequenceMatcher(
            None,
            original_value,
            candidate_value,
        ).ratio()

    @staticmethod
    def _exact_match(
        original_value: Any,
        candidate_value: Any,
    ) -> float:
        """Return one for an exact normalized match."""

        original = str(original_value or "").strip().lower()
        candidate = str(candidate_value or "").strip().lower()

        if not original and not candidate:
            return 1.0

        return 1.0 if original == candidate else 0.0

    @staticmethod
    def _element_center(
        element: dict[str, Any],
    ) -> tuple[float, float]:
        """Return element center coordinates."""

        if (
            element.get("center_x") is not None
            and element.get("center_y") is not None
        ):
            return (
                float(element["center_x"]),
                float(element["center_y"]),
            )

        x = float(element.get("x", 0.0))
        y = float(element.get("y", 0.0))
        width = float(element.get("width", 0.0))
        height = float(element.get("height", 0.0))

        return (
            x + width / 2.0,
            y + height / 2.0,
        )

    @staticmethod
    def _clip(value: float) -> float:
        """Restrict a score to the range zero to one."""

        return max(0.0, min(float(value), 1.0))