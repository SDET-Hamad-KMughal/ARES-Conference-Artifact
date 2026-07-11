"""Fault-injection evaluation for the ARES self-healing engine."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.common.by import By

from self_healing.healer import LocatorHealer
from web_environment.browser_env import BrowserEnvironment
from web_environment.dom_extractor import DOMExtractor


ORIGINAL_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>ARES Fault Injection</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            padding: 40px;
        }

        .container {
            width: 500px;
        }

        .primary-button {
            width: 140px;
            height: 44px;
            margin-top: 20px;
        }

        .support-link {
            display: block;
            margin-top: 30px;
        }
    </style>
</head>
<body>
    <main class="container">
        <h1>Account Login</h1>

        <form>
            <label for="username">Username</label>

            <input
                id="username"
                name="username"
                type="text"
                placeholder="Enter username"
                aria-label="Username">

            <button
                id="login-button"
                name="login"
                type="button"
                role="button"
                class="btn primary-button"
                aria-label="Sign in">
                Sign in
            </button>
        </form>

        <a
            id="support-link"
            class="support-link"
            href="#support"
            aria-label="Contact support">
            Contact support
        </a>
    </main>
</body>
</html>
"""


FAULT_TEMPLATES = {
    "id_change": """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>ARES Fault Injection</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 40px; }}
        .container {{ width: 500px; }}
        .primary-button {{ width: 140px; height: 44px; margin-top: 20px; }}
        .support-link {{ display: block; margin-top: 30px; }}
    </style>
</head>
<body>
    <main class="container">
        <h1>Account Login</h1>

        <form>
            <label for="username">Username</label>

            <input
                id="username"
                name="username"
                type="text"
                placeholder="Enter username"
                aria-label="Username">

            <button
                id="signin-button"
                name="login"
                type="button"
                role="button"
                class="btn primary-button"
                aria-label="Sign in">
                Sign in
            </button>
        </form>

        <a id="support-link" class="support-link"
           href="#support" aria-label="Contact support">
            Contact support
        </a>
    </main>
</body>
</html>
""",
    "text_change": """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>ARES Fault Injection</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 40px; }}
        .container {{ width: 500px; }}
        .primary-button {{ width: 140px; height: 44px; margin-top: 20px; }}
        .support-link {{ display: block; margin-top: 30px; }}
    </style>
</head>
<body>
    <main class="container">
        <h1>Account Login</h1>

        <form>
            <label for="username">Username</label>

            <input
                id="username"
                name="username"
                type="text"
                placeholder="Enter username"
                aria-label="Username">

            <button
                id="signin-button"
                name="login"
                type="button"
                role="button"
                class="btn primary-button"
                aria-label="Log in">
                Log in
            </button>
        </form>

        <a id="support-link" class="support-link"
           href="#support" aria-label="Contact support">
            Contact support
        </a>
    </main>
</body>
</html>
""",
    "class_change": """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>ARES Fault Injection</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 40px; }}
        .container {{ width: 500px; }}
        .replacement-button {{ width: 140px; height: 44px; margin-top: 20px; }}
        .support-link {{ display: block; margin-top: 30px; }}
    </style>
</head>
<body>
    <main class="container">
        <h1>Account Login</h1>

        <form>
            <label for="username">Username</label>

            <input
                id="username"
                name="username"
                type="text"
                placeholder="Enter username"
                aria-label="Username">

            <button
                id="signin-button"
                name="login"
                type="button"
                role="button"
                class="action replacement-button"
                aria-label="Sign in">
                Sign in
            </button>
        </form>

        <a id="support-link" class="support-link"
           href="#support" aria-label="Contact support">
            Contact support
        </a>
    </main>
</body>
</html>
""",
    "structure_change": """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>ARES Fault Injection</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 40px; }}
        .container {{ width: 500px; }}
        .primary-button {{ width: 140px; height: 44px; margin-top: 20px; }}
        .support-link {{ display: block; margin-top: 30px; }}
    </style>
</head>
<body>
    <main class="container">
        <h1>Account Login</h1>

        <section>
            <div class="form-wrapper">
                <form>
                    <label for="username">Username</label>

                    <input
                        id="username"
                        name="username"
                        type="text"
                        placeholder="Enter username"
                        aria-label="Username">

                    <div class="button-wrapper">
                        <button
                            id="signin-button"
                            name="login"
                            type="button"
                            role="button"
                            class="btn primary-button"
                            aria-label="Sign in">
                            Sign in
                        </button>
                    </div>
                </form>
            </div>
        </section>

        <a id="support-link" class="support-link"
           href="#support" aria-label="Contact support">
            Contact support
        </a>
    </main>
</body>
</html>
""",
    "position_change": """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>ARES Fault Injection</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 40px; }}
        .container {{ width: 800px; }}
        .primary-button {{
            width: 140px;
            height: 44px;
            margin-top: 220px;
            margin-left: 300px;
        }}
        .support-link {{ display: block; margin-top: 30px; }}
    </style>
</head>
<body>
    <main class="container">
        <h1>Account Login</h1>

        <form>
            <label for="username">Username</label>

            <input
                id="username"
                name="username"
                type="text"
                placeholder="Enter username"
                aria-label="Username">

            <button
                id="signin-button"
                name="login"
                type="button"
                role="button"
                class="btn primary-button"
                aria-label="Sign in">
                Sign in
            </button>
        </form>

        <a id="support-link" class="support-link"
           href="#support" aria-label="Contact support">
            Contact support
        </a>
    </main>
</body>
</html>
""",
    "combined_fault": """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>ARES Fault Injection</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 40px; }}
        .container {{ width: 800px; }}
        .replacement-button {{
            width: 150px;
            height: 46px;
            margin-top: 140px;
            margin-left: 180px;
        }}
        .support-link {{ display: block; margin-top: 30px; }}
    </style>
</head>
<body>
    <main class="container">
        <h1>Account Login</h1>

        <section>
            <div class="form-wrapper">
                <form>
                    <label for="username">Username</label>

                    <input
                        id="username"
                        name="username"
                        type="text"
                        placeholder="Enter username"
                        aria-label="Username">

                    <div class="button-wrapper">
                        <button
                            id="account-access-button"
                            name="login"
                            type="button"
                            role="button"
                            class="action replacement-button"
                            aria-label="Log in">
                            Log in
                        </button>
                    </div>
                </form>
            </div>
        </section>

        <a id="support-link" class="support-link"
           href="#support" aria-label="Contact support">
            Contact support
        </a>
    </main>
</body>
</html>
""",
}


@dataclass
class FaultInjectionResult:
    """Result from one injected locator fault."""

    fault_type: str
    old_locator_failed: bool
    healed: bool
    selected_score: float
    selected_element_id: str
    replacement_strategy: str
    replacement_value: str
    replacement_executed: bool
    threshold: float


def write_page(path: Path, html: str) -> None:
    """Write an HTML fixture to disk."""

    path.write_text(html, encoding="utf-8")


def find_element_by_id(
    elements: list[dict[str, Any]],
    element_id: str,
) -> dict[str, Any]:
    """Return one extracted element using its ID."""

    for element in elements:
        if element.get("id") == element_id:
            return element

    raise RuntimeError(f"DOM element was not found: {element_id}")


def execute_replacement_locator(
    browser: BrowserEnvironment,
    locator: dict[str, str],
) -> None:
    """Execute a generated replacement locator."""

    strategy = locator["strategy"]
    value = locator["value"]

    strategy_mapping = {
        "id": By.ID,
        "name": By.NAME,
        "css selector": By.CSS_SELECTOR,
        "xpath": By.XPATH,
    }

    by = strategy_mapping.get(strategy)

    if by is None:
        raise ValueError(
            f"Unsupported replacement strategy: {strategy}"
        )

    browser.click(by, value)


def run_fault_injection(
    browser: BrowserEnvironment,
    extractor: DOMExtractor,
    healer: LocatorHealer,
    original_element: dict[str, Any],
    fault_type: str,
    fault_page: Path,
) -> FaultInjectionResult:
    """Run one locator fault and healing attempt."""

    browser.open(fault_page.resolve().as_uri())

    try:
        browser.click(By.ID, "login-button")
        old_locator_failed = False
    except (TimeoutException, NoSuchElementException):
        old_locator_failed = True

    candidates = extractor.extract_interactive_elements()

    driver = browser.driver

    if driver is None:
        raise RuntimeError("Browser driver is unavailable.")

    viewport_width = float(
        driver.execute_script("return window.innerWidth;")
    )

    viewport_height = float(
        driver.execute_script("return window.innerHeight;")
    )

    healing_result = healer.heal(
        original_element=original_element,
        candidates=candidates,
        viewport_width=viewport_width,
        viewport_height=viewport_height,
    )

    replacement_executed = False
    replacement_strategy = ""
    replacement_value = ""

    if (
        healing_result.healed
        and healing_result.replacement_locator is not None
    ):
        replacement_strategy = (
            healing_result.replacement_locator["strategy"]
        )

        replacement_value = (
            healing_result.replacement_locator["value"]
        )

        execute_replacement_locator(
            browser,
            healing_result.replacement_locator,
        )

        replacement_executed = True

    selected_element_id = ""

    if healing_result.selected_candidate is not None:
        selected_element_id = str(
            healing_result.selected_candidate.get("id", "")
        )

    return FaultInjectionResult(
        fault_type=fault_type,
        old_locator_failed=old_locator_failed,
        healed=healing_result.healed,
        selected_score=healing_result.selected_score,
        selected_element_id=selected_element_id,
        replacement_strategy=replacement_strategy,
        replacement_value=replacement_value,
        replacement_executed=replacement_executed,
        threshold=healer.threshold,
    )


def save_results(
    results: list[FaultInjectionResult],
    output_path: str | Path,
) -> Path:
    """Save fault-injection results to CSV."""

    if not results:
        raise ValueError("No fault-injection results were provided.")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(asdict(results[0]).keys())

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for result in results:
            writer.writerow(asdict(result))

    return path


def print_summary(
    results: list[FaultInjectionResult],
) -> None:
    """Print aggregate healing measurements."""

    healed_count = sum(
        1 for result in results if result.healed
    )

    execution_count = sum(
        1 for result in results if result.replacement_executed
    )

    average_score = sum(
        result.selected_score for result in results
    ) / len(results)

    print("\nFault-injection summary")
    print("-----------------------")
    print(f"Injected faults: {len(results)}")
    print(f"Healed faults: {healed_count}")
    print(
        f"Healing success rate: "
        f"{healed_count / len(results):.2%}"
    )
    print(f"Executed replacements: {execution_count}")
    print(f"Average selected score: {average_score:.4f}")

    for result in results:
        print(asdict(result))


def parse_arguments() -> argparse.Namespace:
    """Parse command-line options."""

    parser = argparse.ArgumentParser(
        description="Evaluate ARES locator healing using injected faults."
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=0.7,
        help="Locator-healing acceptance threshold.",
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run Chrome without displaying the browser.",
    )

    parser.add_argument(
        "--output",
        default="results/evaluation/fault_injection_results.csv",
        help="Fault-injection CSV output path.",
    )

    return parser.parse_args()


def main() -> None:
    """Execute all configured fault-injection scenarios."""

    args = parse_arguments()

    fixture_directory = Path(
        "results/evaluation/fault_injection_pages"
    )

    fixture_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    original_path = fixture_directory / "original.html"

    write_page(
        original_path,
        ORIGINAL_HTML,
    )

    fault_paths: dict[str, Path] = {}

    for fault_type, template in FAULT_TEMPLATES.items():
        fault_path = fixture_directory / f"{fault_type}.html"

        write_page(
            fault_path,
            template,
        )

        fault_paths[fault_type] = fault_path

    browser = BrowserEnvironment(
        headless=args.headless,
        timeout=3,
    )

    results: list[FaultInjectionResult] = []

    try:
        browser.start()

        driver = browser.driver

        if driver is None:
            raise RuntimeError("Browser driver was not initialized.")

        extractor = DOMExtractor(driver)
        healer = LocatorHealer(threshold=args.threshold)

        browser.open(original_path.resolve().as_uri())

        original_elements = (
            extractor.extract_interactive_elements()
        )

        original_element = find_element_by_id(
            original_elements,
            "login-button",
        )

        for fault_type, fault_path in fault_paths.items():
            print(f"Running fault: {fault_type}")

            result = run_fault_injection(
                browser=browser,
                extractor=extractor,
                healer=healer,
                original_element=original_element,
                fault_type=fault_type,
                fault_page=fault_path,
            )

            results.append(result)

    finally:
        browser.close()

    output_path = save_results(
        results,
        args.output,
    )

    print_summary(results)
    print(f"Results saved to: {output_path}")


if __name__ == "__main__":
    main()