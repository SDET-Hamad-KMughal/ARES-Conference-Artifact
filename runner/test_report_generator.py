"""Smoke test for the ARES ReportGenerator."""

from pathlib import Path

from runner.core.evaluation_pipeline import EvaluationPipeline
from runner.core.report_generator import ReportGenerator


EVALUATION_JSON = Path(
    "runner/results/angular/evaluation/"
    "angular_route_exploration_evaluation.json"
)

REPORT_OUTPUT = Path(
    "runner/results/angular/report/"
    "evaluation_report.txt"
)


def main() -> None:
    pipeline = EvaluationPipeline()

    evaluation = pipeline.load_json(
        EVALUATION_JSON
    )

    generator = ReportGenerator()

    report = generator.generate(
        evaluation
    )

    output_path = generator.save(
        report,
        REPORT_OUTPUT,
    )

    print("=" * 70)
    print("ARES Report Generator Smoke Test")
    print("=" * 70)
    print(report)
    print("=" * 70)
    print(f"Report saved: {output_path}")
    print("=" * 70)

    assert output_path.exists()

    assert "ARES CONFERENCE ARTIFACT EVALUATION REPORT" in report
    assert "Angular Route Exploration" in report
    assert "PASS" in report
    assert "100.00%" in report
    assert "States discovered: 5" in report
    assert "Transitions created: 4" in report

    print("Report generator test passed.")


if __name__ == "__main__":
    main()