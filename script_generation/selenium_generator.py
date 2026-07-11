"""Generate executable Selenium test scripts from ARES action traces."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass
class GeneratedScript:
    """Generated Selenium script and its output location."""

    code: str
    output_path: Path


class SeleniumScriptGenerator:
    """Convert ARES browser actions into a Selenium Python test."""

    SUPPORTED_STRATEGIES = {
        "id": "By.ID",
        "name": "By.NAME",
        "xpath": "By.XPATH",
        "css selector": "By.CSS_SELECTOR",
        "link text": "By.LINK_TEXT",
        "partial link text": "By.PARTIAL_LINK_TEXT",
        "tag name": "By.TAG_NAME",
        "class name": "By.CLASS_NAME",
    }

    def __init__(
        self,
        test_name: str = "test_generated_ares_flow",
        timeout: int = 15,
        headless: bool = False,
    ) -> None:
        self.test_name = self._sanitize_function_name(test_name)
        self.timeout = timeout
        self.headless = headless

    def generate(
        self,
        start_url: str,
        actions: Iterable[dict[str, Any]],
        output_path: str | Path,
        assertions: Iterable[dict[str, Any]] | None = None,
    ) -> GeneratedScript:
        """Generate and save a Selenium Python test script."""

        action_list = list(actions)
        assertion_list = list(assertions or [])

        code = self._build_script(
            start_url=start_url,
            actions=action_list,
            assertions=assertion_list,
        )

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(code, encoding="utf-8")

        return GeneratedScript(
            code=code,
            output_path=path,
        )

    def _build_script(
        self,
        start_url: str,
        actions: list[dict[str, Any]],
        assertions: list[dict[str, Any]],
    ) -> str:
        """Build the complete Python source code."""

        lines = [
            '"""Generated automatically by the ARES framework."""',
            "",
            "from selenium import webdriver",
            "from selenium.webdriver import ChromeOptions",
            "from selenium.webdriver.common.by import By",
            "from selenium.webdriver.support import expected_conditions as EC",
            "from selenium.webdriver.support.ui import Select, WebDriverWait",
            "",
            "",
            f"def {self.test_name}() -> None:",
            "    options = ChromeOptions()",
        ]

        if self.headless:
            lines.append('    options.add_argument("--headless=new")')

        lines.extend(
            [
                '    options.add_argument("--window-size=1440,900")',
                "    driver = webdriver.Chrome(options=options)",
                f"    wait = WebDriverWait(driver, {self.timeout})",
                "",
                "    try:",
                f"        driver.get({start_url!r})",
                "",
            ]
        )

        for index, action in enumerate(actions, start=1):
            lines.extend(
                self._generate_action_lines(
                    action=action,
                    action_number=index,
                )
            )

        for assertion in assertions:
            lines.extend(self._generate_assertion_lines(assertion))

        lines.extend(
            [
                "    finally:",
                "        driver.quit()",
                "",
                "",
                'if __name__ == "__main__":',
                f"    {self.test_name}()",
                "",
            ]
        )

        return "\n".join(lines)

    def _generate_action_lines(
        self,
        action: dict[str, Any],
        action_number: int,
    ) -> list[str]:
        """Convert one action record into Selenium code."""

        action_type = str(action.get("type", "")).lower()

        lines = [
            f"        # Action {action_number}: {action_type or 'unknown'}"
        ]

        if action_type == "click":
            locator = self._locator_expression(action)

            lines.extend(
                [
                    f"        element = wait.until(",
                    f"            EC.element_to_be_clickable({locator})",
                    "        )",
                    "        element.click()",
                    "",
                ]
            )

        elif action_type == "type":
            locator = self._locator_expression(action)
            text = str(action.get("value", "ARES test input"))

            lines.extend(
                [
                    f"        element = wait.until(",
                    f"            EC.visibility_of_element_located({locator})",
                    "        )",
                    "        element.clear()",
                    f"        element.send_keys({text!r})",
                    "",
                ]
            )

        elif action_type == "select":
            locator = self._locator_expression(action)
            value = str(action.get("value", ""))
            selection_type = str(
                action.get("selection_type", "visible_text")
            )

            lines.extend(
                [
                    f"        element = wait.until(",
                    f"            EC.presence_of_element_located({locator})",
                    "        )",
                    "        select = Select(element)",
                ]
            )

            if selection_type == "value":
                lines.append(f"        select.select_by_value({value!r})")
            elif selection_type == "index":
                lines.append(f"        select.select_by_index({int(value)})")
            else:
                lines.append(
                    f"        select.select_by_visible_text({value!r})"
                )

            lines.append("")

        elif action_type == "scroll_down":
            lines.extend(
                [
                    '        driver.execute_script("window.scrollBy(0, 600);")',
                    "",
                ]
            )

        elif action_type == "scroll_up":
            lines.extend(
                [
                    '        driver.execute_script("window.scrollBy(0, -600);")',
                    "",
                ]
            )

        elif action_type == "back":
            lines.extend(
                [
                    "        driver.back()",
                    "",
                ]
            )

        elif action_type == "refresh":
            lines.extend(
                [
                    "        driver.refresh()",
                    "",
                ]
            )

        else:
            lines.extend(
                [
                    "        # Unsupported or observational action skipped.",
                    "",
                ]
            )

        return lines

    def _generate_assertion_lines(
        self,
        assertion: dict[str, Any],
    ) -> list[str]:
        """Generate one assertion block."""

        assertion_type = str(assertion.get("type", "")).lower()
        expected = assertion.get("expected", "")

        lines = ["        # Generated assertion"]

        if assertion_type == "url_contains":
            lines.append(
                f"        assert {str(expected)!r} in driver.current_url"
            )

        elif assertion_type == "title_contains":
            lines.append(
                f"        assert {str(expected)!r} in driver.title"
            )

        elif assertion_type == "element_visible":
            locator = self._locator_expression(assertion)

            lines.extend(
                [
                    f"        assert wait.until(",
                    f"            EC.visibility_of_element_located({locator})",
                    "        ).is_displayed()",
                ]
            )

        elif assertion_type == "text_present":
            lines.append(
                f"        assert {str(expected)!r} in driver.page_source"
            )

        else:
            lines.append(
                "        # Unsupported assertion type was skipped."
            )

        lines.append("")
        return lines

    def _locator_expression(
        self,
        record: dict[str, Any],
    ) -> str:
        """Return a Selenium locator tuple expression."""

        locator = record.get("locator")

        if isinstance(locator, dict):
            strategy = str(locator.get("strategy", "")).lower()
            value = str(locator.get("value", ""))
        else:
            strategy = str(record.get("strategy", "")).lower()
            value = str(record.get("locator_value", ""))

        if strategy not in self.SUPPORTED_STRATEGIES:
            raise ValueError(
                f"Unsupported Selenium locator strategy: {strategy}"
            )

        if not value:
            raise ValueError("Locator value cannot be empty.")

        by_expression = self.SUPPORTED_STRATEGIES[strategy]

        return f"({by_expression}, {value!r})"

    @staticmethod
    def _sanitize_function_name(value: str) -> str:
        """Convert a supplied name into a valid Python function name."""

        cleaned = "".join(
            character if character.isalnum() else "_"
            for character in value.strip()
        )

        cleaned = cleaned.strip("_")

        if not cleaned:
            cleaned = "test_generated_ares_flow"

        if cleaned[0].isdigit():
            cleaned = f"test_{cleaned}"

        if not cleaned.startswith("test_"):
            cleaned = f"test_{cleaned}"

        return cleaned