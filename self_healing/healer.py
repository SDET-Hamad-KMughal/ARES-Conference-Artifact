"""Proactive locator self-healing engine for ARES."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Optional

from self_healing.similarity import SimilarityEngine


@dataclass(frozen=True)
class SimilarityWeights:
    """Weights for the ARES composite locator-similarity equation."""

    textual: float = 0.4
    structural: float = 0.3
    spatial: float = 0.3

    def __post_init__(self) -> None:
        values = (
            self.textual,
            self.structural,
            self.spatial,
        )

        if any(value < 0.0 for value in values):
            raise ValueError("Similarity weights cannot be negative.")

        total = sum(values)

        if abs(total - 1.0) > 1e-9:
            raise ValueError(
                "Similarity weights must sum to 1.0. "
                f"Received total: {total}"
            )


@dataclass
class RankedCandidate:
    """One candidate together with its similarity scores."""

    candidate: dict[str, Any]
    textual_similarity: float
    structural_similarity: float
    spatial_similarity: float
    total_similarity: float
    accepted: bool

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable ranking record."""
        return asdict(self)


@dataclass
class HealingResult:
    """Result produced by proactive locator healing."""

    healed: bool
    threshold: float
    original_element: dict[str, Any]
    selected_candidate: Optional[dict[str, Any]]
    replacement_locator: Optional[dict[str, str]]
    selected_score: float
    rankings: list[RankedCandidate]
    reason: str

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable healing result."""

        return {
            "healed": self.healed,
            "threshold": self.threshold,
            "original_element": self.original_element,
            "selected_candidate": self.selected_candidate,
            "replacement_locator": self.replacement_locator,
            "selected_score": self.selected_score,
            "rankings": [
                ranking.to_dict()
                for ranking in self.rankings
            ],
            "reason": self.reason,
        }


class LocatorHealer:
    """
    Rank replacement candidates using the ARES weighted equation.

    sigma_total =
        w1 * sigma_text
        + w2 * sigma_struct
        + w3 * sigma_prox
    """

    def __init__(
        self,
        similarity_engine: Optional[SimilarityEngine] = None,
        weights: Optional[SimilarityWeights] = None,
        threshold: float = 0.7,
    ) -> None:
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(
                "Acceptance threshold must be between 0 and 1."
            )

        self.similarity_engine = (
            similarity_engine or SimilarityEngine()
        )
        self.weights = weights or SimilarityWeights()
        self.threshold = threshold

    def calculate_total_similarity(
        self,
        textual_similarity: float,
        structural_similarity: float,
        spatial_similarity: float,
    ) -> float:
        """Calculate the weighted ARES similarity score."""

        scores = (
            textual_similarity,
            structural_similarity,
            spatial_similarity,
        )

        if any(not 0.0 <= score <= 1.0 for score in scores):
            raise ValueError(
                "All component scores must be between 0 and 1."
            )

        total = (
            self.weights.textual * textual_similarity
            + self.weights.structural * structural_similarity
            + self.weights.spatial * spatial_similarity
        )

        return max(0.0, min(float(total), 1.0))

    def rank_candidates(
        self,
        original_element: dict[str, Any],
        candidates: Iterable[dict[str, Any]],
        viewport_width: float,
        viewport_height: float,
    ) -> list[RankedCandidate]:
        """Score and rank all candidate replacement elements."""

        rankings: list[RankedCandidate] = []

        for candidate in candidates:
            components = (
                self.similarity_engine.calculate_components(
                    original=original_element,
                    candidate=candidate,
                    viewport_width=viewport_width,
                    viewport_height=viewport_height,
                )
            )

            total_similarity = self.calculate_total_similarity(
                textual_similarity=components["semantic"],
                structural_similarity=components["structural"],
                spatial_similarity=components["spatial"],
            )

            rankings.append(
                RankedCandidate(
                    candidate=candidate,
                    textual_similarity=components["semantic"],
                    structural_similarity=components["structural"],
                    spatial_similarity=components["spatial"],
                    total_similarity=total_similarity,
                    accepted=total_similarity >= self.threshold,
                )
            )

        rankings.sort(
            key=lambda ranking: ranking.total_similarity,
            reverse=True,
        )

        return rankings

    def heal(
        self,
        original_element: dict[str, Any],
        candidates: Iterable[dict[str, Any]],
        viewport_width: float,
        viewport_height: float,
    ) -> HealingResult:
        """
        Select the highest-scoring acceptable replacement element.
        """

        rankings = self.rank_candidates(
            original_element=original_element,
            candidates=candidates,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
        )

        if not rankings:
            return HealingResult(
                healed=False,
                threshold=self.threshold,
                original_element=original_element,
                selected_candidate=None,
                replacement_locator=None,
                selected_score=0.0,
                rankings=[],
                reason="No replacement candidates were provided.",
            )

        best_match = rankings[0]

        if not best_match.accepted:
            return HealingResult(
                healed=False,
                threshold=self.threshold,
                original_element=original_element,
                selected_candidate=None,
                replacement_locator=None,
                selected_score=best_match.total_similarity,
                rankings=rankings,
                reason=(
                    "The highest candidate score did not meet "
                    "the acceptance threshold."
                ),
            )

        replacement_locator = self.generate_locator(
            best_match.candidate
        )

        if replacement_locator is None:
            return HealingResult(
                healed=False,
                threshold=self.threshold,
                original_element=original_element,
                selected_candidate=best_match.candidate,
                replacement_locator=None,
                selected_score=best_match.total_similarity,
                rankings=rankings,
                reason=(
                    "A candidate passed the threshold, but no "
                    "supported replacement locator could be generated."
                ),
            )

        return HealingResult(
            healed=True,
            threshold=self.threshold,
            original_element=original_element,
            selected_candidate=best_match.candidate,
            replacement_locator=replacement_locator,
            selected_score=best_match.total_similarity,
            rankings=rankings,
            reason="Replacement candidate accepted.",
        )

    @staticmethod
    def generate_locator(
        candidate: dict[str, Any],
    ) -> Optional[dict[str, str]]:
        """
        Generate a stable Selenium locator for a candidate.

        Locator preference:
        1. ID
        2. name
        3. aria-label
        4. CSS selector
        5. XPath
        """

        element_id = str(candidate.get("id", "")).strip()

        if element_id:
            return {
                "strategy": "id",
                "value": element_id,
            }

        name = str(candidate.get("name", "")).strip()

        if name:
            return {
                "strategy": "name",
                "value": name,
            }

        aria_label = str(
            candidate.get("aria_label", "")
        ).strip()

        if aria_label:
            escaped_label = aria_label.replace('"', '\\"')

            return {
                "strategy": "css selector",
                "value": f'[aria-label="{escaped_label}"]',
            }

        css_selector = str(
            candidate.get("css_selector", "")
        ).strip()

        if css_selector:
            return {
                "strategy": "css selector",
                "value": css_selector,
            }

        xpath = str(candidate.get("xpath", "")).strip()

        if xpath:
            return {
                "strategy": "xpath",
                "value": xpath,
            }

        return None