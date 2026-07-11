"""Smoke test for the ARES Selenium script generator."""

from pathlib import Path

from script_generation.selenium_generator import SeleniumScriptGenerator


def main() -> None:
    actions = [
        {
            "type": "click",
            "locator": {
                "strategy": "css selector",
                "value": "a",
            },
        }
    ]

    assertions = [
        {
            "type": "url_contains",
            "expected": "iana.org",
        }
    ]

    output_path = Path(
        "generated_tests/test_example_domain_generated.py"
    )

    generator = SeleniumScriptGenerator(
        test_name="example_domain_flow",
        headless=True,
    )

    generated = generator.generate(
        start_url="https://example.com",
        actions=actions,
        assertions=assertions,
        output_path=output_path,
    )

    print("Generated file:", generated.output_path)
    print(generated.code)

    assert generated.output_path.exists()
    assert "driver.get('https://example.com')" in generated.code
    assert "element.click()" in generated.code
    assert "iana.org" in generated.code

    print("Selenium generator test passed.")


if __name__ == "__main__":
    main()