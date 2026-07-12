"""ARES lightweight oracle engine.

The oracle engine evaluates whether a browser action produced the expected
result. It combines URL validation, expected-text detection, and visible error
detection into one structured outcome.
"""

import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class OracleResult:
    """Represent the outcome of one oracle evaluation."""

    passed: bool
    score: float
    expected_url: Optional[str]
    actual_url: str
    expected_text: Optional[str]
    url_match: Optional[bool]
    success_text_found: Optional[bool]
    error_detected: bool
    detected_errors: List[str]
    reason: str


class OracleEngine:
    """Evaluate browser outcomes using lightweight deterministic oracles."""

    DEFAULT_ERROR_INDICATORS = (
        "404",
        "500",
        "error",
        "failed",
        "failure",
        "exception",
        "unauthorized",
        "forbidden",
        "not found",
        "internal server error",
    )

    ERROR_PHRASES = (
        "internal server error",
        "page not found",
        "resource not found",
        "access denied",
        "request failed",
        "operation failed",
        "unexpected error",
        "application error",
        "server error",
        "uncaught exception",
        "stack trace",
        "unauthorized",
        "forbidden",
    )

    STATUS_CODE_PATTERNS = (
        r"\b404\s+(?:error|not found)\b",
        r"\b500\s+(?:error|internal server error)\b",
        r"\bhttp\s+404\b",
        r"\bhttp\s+500\b",
        r"\berror\s+404\b",
        r"\berror\s+500\b",
    )

    def __init__(
        self,
        error_indicators: Optional[Iterable[str]] = None,
    ) -> None:
        """
        Initialize the oracle engine.

        Args:
            error_indicators: Optional custom failure indicators.
        """

        indicators = (
            error_indicators
            if error_indicators is not None
            else self.DEFAULT_ERROR_INDICATORS
        )

        self.error_indicators = tuple(
            indicator.strip().lower()
            for indicator in indicators
            if indicator.strip()
        )

    def evaluate(
        self,
        driver: Any,
        expected_url: Optional[str] = None,
        expected_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate the current browser page.

        Args:
            driver: Active Selenium WebDriver instance.
            expected_url: Expected URL fragment or complete URL.
            expected_text: Expected visible page text.

        Returns:
            Structured oracle result dictionary.
        """

        actual_url = driver.current_url

        body_text = driver.execute_script(
            """
            return document.body
                ? document.body.innerText
                : "";
            """
        ) or ""

        normalized_body_text = self._normalize_text(
            body_text
        )

        url_match = self._evaluate_url(
            actual_url=actual_url,
            expected_url=expected_url,
        )

        success_text_found = self._evaluate_text(
            body_text=body_text,
            expected_text=expected_text,
        )

        detected_errors = self._detect_errors(
            normalized_body_text
        )

        error_detected = bool(detected_errors)

        passed = self._determine_passed(
            url_match=url_match,
            success_text_found=success_text_found,
            error_detected=error_detected,
        )

        score = self._calculate_score(
            url_match=url_match,
            success_text_found=success_text_found,
            error_detected=error_detected,
        )

        reason = self._build_reason(
            passed=passed,
            url_match=url_match,
            success_text_found=success_text_found,
            error_detected=error_detected,
            detected_errors=detected_errors,
        )

        result = OracleResult(
            passed=passed,
            score=score,
            expected_url=expected_url,
            actual_url=actual_url,
            expected_text=expected_text,
            url_match=url_match,
            success_text_found=success_text_found,
            error_detected=error_detected,
            detected_errors=detected_errors,
            reason=reason,
        )

        return asdict(result)

    @staticmethod
    def _normalize_text(
        text: str,
    ) -> str:
        """Normalize visible page text for deterministic matching."""

        return " ".join(
            text.lower().split()
        )

    @staticmethod
    def _evaluate_url(
        actual_url: str,
        expected_url: Optional[str],
    ) -> Optional[bool]:
        """Evaluate whether the actual URL matches the expectation."""

        if expected_url is None:
            return None

        normalized_expected = expected_url.strip()

        if not normalized_expected:
            return None

        return normalized_expected in actual_url

    @staticmethod
    def _evaluate_text(
        body_text: str,
        expected_text: Optional[str],
    ) -> Optional[bool]:
        """Evaluate whether expected text is visible on the page."""

        if expected_text is None:
            return None

        normalized_expected = expected_text.strip().lower()

        if not normalized_expected:
            return None

        return normalized_expected in body_text.lower()

    def _detect_errors(
        self,
        normalized_body_text: str,
    ) -> List[str]:
        """
        Detect genuine visible error messages.

        Standalone numbers such as 404 or 500 are not treated as errors because
        they may appear in prices, identifiers, product descriptions, or phone
        numbers. Numeric status codes are accepted only when they appear in a
        recognizable error phrase.
        """

        detected: List[str] = []

        for phrase in self.ERROR_PHRASES:
            if phrase in normalized_body_text:
                detected.append(phrase)

        for pattern in self.STATUS_CODE_PATTERNS:
            match = re.search(
                pattern,
                normalized_body_text,
                flags=re.IGNORECASE,
            )

            if match:
                detected.append(
                    match.group(0).lower()
                )

        custom_indicators = [
            indicator
            for indicator in self.error_indicators
            if indicator not in {"404", "500"}
            and indicator not in self.ERROR_PHRASES
        ]

        for indicator in custom_indicators:
            if self._contains_indicator(
                normalized_body_text,
                indicator,
            ):
                detected.append(indicator)

        return list(
            dict.fromkeys(detected)
        )

    @staticmethod
    def _contains_indicator(
        normalized_body_text: str,
        indicator: str,
    ) -> bool:
        """
        Match an indicator as a phrase or complete word.

        This avoids substring false positives such as detecting "error" inside
        an unrelated longer word.
        """

        escaped_indicator = re.escape(indicator)

        pattern = (
            rf"(?<!\w){escaped_indicator}(?!\w)"
        )

        return bool(
            re.search(
                pattern,
                normalized_body_text,
                flags=re.IGNORECASE,
            )
        )

    @staticmethod
    def _determine_passed(
        url_match: Optional[bool],
        success_text_found: Optional[bool],
        error_detected: bool,
    ) -> bool:
        """Determine the overall oracle outcome."""

        checks: List[bool] = []

        if url_match is not None:
            checks.append(url_match)

        if success_text_found is not None:
            checks.append(success_text_found)

        if not checks:
            checks.append(True)

        return all(checks) and not error_detected

    @staticmethod
    def _calculate_score(
        url_match: Optional[bool],
        success_text_found: Optional[bool],
        error_detected: bool,
    ) -> float:
        """Calculate a normalized confidence score."""

        scores: List[float] = []

        if url_match is not None:
            scores.append(
                1.0 if url_match else 0.0
            )

        if success_text_found is not None:
            scores.append(
                1.0 if success_text_found else 0.0
            )

        scores.append(
            0.0 if error_detected else 1.0
        )

        return round(
            sum(scores) / len(scores),
            2,
        )

    @staticmethod
    def _build_reason(
        passed: bool,
        url_match: Optional[bool],
        success_text_found: Optional[bool],
        error_detected: bool,
        detected_errors: List[str],
    ) -> str:
        """Build a human-readable oracle explanation."""

        reasons: List[str] = []

        if url_match is True:
            reasons.append(
                "Expected URL reached"
            )

        elif url_match is False:
            reasons.append(
                "Expected URL was not reached"
            )

        if success_text_found is True:
            reasons.append(
                "Expected text was found"
            )

        elif success_text_found is False:
            reasons.append(
                "Expected text was not found"
            )

        if error_detected:
            reasons.append(
                "Error indicators detected: "
                + ", ".join(detected_errors)
            )

        else:
            reasons.append(
                "No error indicators detected"
            )

        prefix = "PASS" if passed else "FAIL"

        return prefix + ": " + "; ".join(reasons)