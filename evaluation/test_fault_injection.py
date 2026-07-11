"""Smoke test for ARES fault-injection evaluation."""

from pathlib import Path

from evaluation.fault_injection import (
    FaultInjectionResult,
    save_results,
)


def main() -> None:
    results = [
        FaultInjectionResult(
            fault_type="id_change",
            old_locator_failed=True,
            healed=True,
            selected_score=0.92,
            selected_element_id="signin-button",
            replacement_strategy="id",
            replacement_value="signin-button",
            replacement_executed=True,
            threshold=0.7,
        )
    ]

    output_path = save_results(
        results,
        "results/evaluation/test_fault_injection.csv",
    )

    assert Path(output_path).exists()
    assert results[0].healed is True
    assert results[0].old_locator_failed is True

    print("Fault-injection utility test passed.")


if __name__ == "__main__":
    main()