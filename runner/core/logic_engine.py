"""ARES lightweight logic engine.

The logic engine converts structured DOM analysis into executable candidate
actions. It does not execute browser actions itself; it only identifies and
ranks actions that may be performed by the ActionExecutor.
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List


@dataclass
class CandidateAction:
    """
    Represents one browser action inferred from the analyzed DOM.
    """

    action_type: str
    selector_type: str
    selector: str
    label: str
    priority: int
    source: str
    metadata: Dict[str, Any]


class LogicEngine:
    """
    Infer candidate browser actions from DOM Analyzer output.
    """

    def __init__(
        self,
        include_hidden: bool = False,
        include_disabled: bool = False,
    ) -> None:
        """
        Initialize the logic engine.

        Args:
            include_hidden: Include elements that are not currently visible.
            include_disabled: Include disabled elements.
        """
        self.include_hidden = include_hidden
        self.include_disabled = include_disabled

    def infer_actions(
        self,
        analysis: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Infer candidate actions from one DOM analysis result.

        Args:
            analysis: Structured output from DOMAnalyzer.analyze().

        Returns:
            Ranked list of candidate action dictionaries.
        """

        actions: List[CandidateAction] = []

        actions.extend(
            self._infer_link_actions(
                analysis.get("links", [])
            )
        )

        actions.extend(
            self._infer_button_actions(
                analysis.get("buttons", [])
            )
        )

        actions.extend(
            self._infer_input_actions(
                analysis.get("inputs", [])
            )
        )

        actions.extend(
            self._infer_form_actions(
                analysis.get("forms", [])
            )
        )

        deduplicated_actions = self._deduplicate(actions)

        ranked_actions = sorted(
            deduplicated_actions,
            key=lambda action: (
                action.priority,
                action.action_type,
                action.selector,
            ),
        )

        return [
            asdict(action)
            for action in ranked_actions
        ]

    def _infer_link_actions(
        self,
        links: List[Dict[str, Any]],
    ) -> List[CandidateAction]:
        """
        Infer click actions from anchor elements.
        """

        actions: List[CandidateAction] = []

        for link in links:
            if not self._is_eligible(link):
                continue

            selector = self._best_selector(link)

            if not selector:
                continue

            label = self._best_label(
                link,
                fallback="Link",
            )

            href = link.get("href")
            raw_href = link.get("raw_href")

            actions.append(
                CandidateAction(
                    action_type="click",
                    selector_type="css",
                    selector=selector,
                    label=label,
                    priority=20,
                    source="link",
                    metadata={
                        "href": href,
                        "raw_href": raw_href,
                        "target": link.get("target"),
                    },
                )
            )

        return actions

    def _infer_button_actions(
        self,
        buttons: List[Dict[str, Any]],
    ) -> List[CandidateAction]:
        """
        Infer click actions from button-like elements.
        """

        actions: List[CandidateAction] = []

        for button in buttons:
            if not self._is_eligible(button):
                continue

            selector = self._best_selector(button)

            if not selector:
                continue

            label = self._best_label(
                button,
                fallback="Button",
            )

            button_type = (
                button.get("type") or ""
            ).lower()

            priority = 10

            if button_type == "submit":
                priority = 5

            actions.append(
                CandidateAction(
                    action_type="click",
                    selector_type="css",
                    selector=selector,
                    label=label,
                    priority=priority,
                    source="button",
                    metadata={
                        "button_type": button_type or None,
                        "value": button.get("value"),
                    },
                )
            )

        return actions

    def _infer_input_actions(
        self,
        inputs: List[Dict[str, Any]],
    ) -> List[CandidateAction]:
        """
        Infer fill, select, or toggle actions from form controls.
        """

        actions: List[CandidateAction] = []

        ignored_input_types = {
            "hidden",
            "submit",
            "button",
            "reset",
            "image",
            "file",
        }

        for input_element in inputs:
            if not self._is_eligible(input_element):
                continue

            selector = self._best_selector(
                input_element
            )

            if not selector:
                continue

            input_type = (
                input_element.get("type") or "text"
            ).lower()

            if input_type in ignored_input_types:
                continue

            label = self._best_label(
                input_element,
                fallback=input_type.capitalize(),
            )

            if input_type in {
                "checkbox",
                "radio",
            }:
                action_type = "toggle"
                priority = 30

            elif input_type == "select":
                action_type = "select"
                priority = 30

            else:
                action_type = "fill"
                priority = 25

            actions.append(
                CandidateAction(
                    action_type=action_type,
                    selector_type="css",
                    selector=selector,
                    label=label,
                    priority=priority,
                    source="input",
                    metadata={
                        "input_type": input_type,
                        "placeholder":
                            input_element.get(
                                "placeholder"
                            ),
                        "name":
                            input_element.get("name"),
                        "required":
                            input_element.get(
                                "required",
                                False,
                            ),
                    },
                )
            )

        return actions

    def _infer_form_actions(
        self,
        forms: List[Dict[str, Any]],
    ) -> List[CandidateAction]:
        """
        Infer submit actions from forms.
        """

        actions: List[CandidateAction] = []

        for form in forms:
            if not self._is_eligible(form):
                continue

            selector = self._best_selector(form)

            if not selector:
                continue

            label = self._best_label(
                form,
                fallback="Submit form",
            )

            actions.append(
                CandidateAction(
                    action_type="submit",
                    selector_type="css",
                    selector=selector,
                    label=label,
                    priority=15,
                    source="form",
                    metadata={
                        "method": form.get("method"),
                        "action": form.get("action"),
                        "input_count":
                            form.get(
                                "input_count",
                                0,
                            ),
                    },
                )
            )

        return actions

    def _is_eligible(
        self,
        element: Dict[str, Any],
    ) -> bool:
        """
        Determine whether an element may become an action.
        """

        if (
            not self.include_hidden
            and not element.get("visible", False)
        ):
            return False

        if (
            not self.include_disabled
            and not element.get("enabled", True)
        ):
            return False

        return True

    @staticmethod
    def _best_selector(
        element: Dict[str, Any],
    ) -> str:
        """
        Select the strongest available CSS selector.
        """

        element_id = element.get("id")

        if element_id:
            return f"#{element_id}"

        css_selector = element.get(
            "css_selector"
        )

        if css_selector:
            return css_selector

        return ""

    @staticmethod
    def _best_label(
        element: Dict[str, Any],
        fallback: str,
    ) -> str:
        """
        Create a readable action label.
        """

        text = (
            element.get("text") or ""
        ).strip()

        if text:
            return text

        placeholder = (
            element.get("placeholder") or ""
        ).strip()

        if placeholder:
            return placeholder

        name = (
            element.get("name") or ""
        ).strip()

        if name:
            return name

        element_id = (
            element.get("id") or ""
        ).strip()

        if element_id:
            return element_id

        return fallback

    @staticmethod
    def _deduplicate(
        actions: List[CandidateAction],
    ) -> List[CandidateAction]:
        """
        Remove repeated actions with the same type and selector.
        """

        unique_actions: Dict[
            tuple[str, str],
            CandidateAction,
        ] = {}

        for action in actions:
            key = (
                action.action_type,
                action.selector,
            )

            existing = unique_actions.get(key)

            if (
                existing is None
                or action.priority < existing.priority
            ):
                unique_actions[key] = action

        return list(unique_actions.values())