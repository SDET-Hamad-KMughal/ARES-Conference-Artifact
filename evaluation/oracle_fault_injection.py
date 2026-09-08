"""Controlled fault-injection evaluation for the ARES oracle."""

import json
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from runner.core.oracle_engine import OracleEngine


OUTPUT_PATH = Path("results/oracle_fault_injection.json")
START_URL = "http://localhost:4200"


def run_case(name, driver, oracle, expected_url=None, expected_text=None):
    result = oracle.evaluate(
        driver=driver,
        expected_url=expected_url,
        expected_text=expected_text,
    )

    return {
        "case": name,
        "passed": result["passed"],
        "score": result["score"],
        "expected_url": result["expected_url"],
        "actual_url": result["actual_url"],
        "expected_text": result["expected_text"],
        "url_match": result["url_match"],
        "success_text_found": result["success_text_found"],
        "error_detected": result["error_detected"],
        "detected_errors": result["detected_errors"],
        "reason": result["reason"],
    }


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    options = Options()
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)
    oracle = OracleEngine()

    results = []

    try:
        driver.get(START_URL)

        results.append(
            run_case(
                name="baseline_normal_page",
                driver=driver,
                oracle=oracle,
                expected_url="localhost:4200",
            )
        )

        driver.execute_script(
            """
            const fault = document.createElement("div");
            fault.id = "ares-injected-fault";
            fault.innerText = "APPLICATION ERROR: injected test failure";
            fault.style.position = "fixed";
            fault.style.top = "10px";
            fault.style.left = "10px";
            fault.style.zIndex = "999999";
            fault.style.padding = "20px";
            fault.style.background = "white";
            fault.style.border = "3px solid black";
            document.body.appendChild(fault);
            """
        )

        results.append(
            run_case(
                name="injected_visible_error",
                driver=driver,
                oracle=oracle,
                expected_url="localhost:4200",
            )
        )

        driver.execute_script(
            """
            const fault = document.getElementById("ares-injected-fault");
            if (fault) {
                fault.remove();
            }
            """
        )

        results.append(
            run_case(
                name="missing_expected_text",
                driver=driver,
                oracle=oracle,
                expected_url="localhost:4200",
                expected_text="ARES_TEXT_THAT_DOES_NOT_EXIST",
            )
        )

    finally:
        driver.quit()

    summary = {
        "total_cases": len(results),
        "passed_cases": sum(1 for r in results if r["passed"]),
        "failed_cases": sum(1 for r in results if not r["passed"]),
        "results": results,
    }

    OUTPUT_PATH.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print()
    print("=" * 60)
    print("ARES Oracle Fault-Injection Evaluation")
    print("=" * 60)

    for result in results:
        status = "PASS" if result["passed"] else "FAIL"

        print(f"\nCase: {result['case']}")
        print(f"Oracle result: {status}")
        print(f"Score: {result['score']}")
        print(f"Error detected: {result['error_detected']}")
        print(f"Reason: {result['reason']}")

    print()
    print("-" * 60)
    print(f"Total cases: {summary['total_cases']}")
    print(f"Passed: {summary['passed_cases']}")
    print(f"Failed: {summary['failed_cases']}")
    print(f"Results saved to: {OUTPUT_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
