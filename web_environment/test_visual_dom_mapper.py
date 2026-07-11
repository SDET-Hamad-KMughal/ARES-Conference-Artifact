from web_environment.browser_env import BrowserEnvironment
from web_environment.visual_dom_mapper import VisualDOMMapper


def main() -> None:
    with BrowserEnvironment(headless=False) as browser:
        browser.open("https://example.com")

        mapper = VisualDOMMapper(browser.driver)

        interactive_elements = mapper.dom_extractor.extract_interactive_elements()

        if not interactive_elements:
            raise RuntimeError("No interactive elements were found.")

        target = interactive_elements[0]

        simulated_detection = {
            "class_name": "link",
            "confidence": 0.99,
            "bbox": [
                target["x"],
                target["y"],
                target["x"] + target["width"],
                target["y"] + target["height"],
            ],
        }

        mapped = mapper.map_detection(simulated_detection)
        candidates = mapper.build_action_candidates([simulated_detection])

        print("Mapped:", mapped["mapped"])
        print("Visual class:", mapped["class_name"])
        print("Confidence:", mapped["confidence"])
        print("DOM element:", mapped["dom_element"])
        print("Action candidates:", candidates)

        assert mapped["mapped"] is True
        assert mapped["dom_element"] is not None
        assert mapped["dom_element"]["tag"] == "a"
        assert candidates[0]["action_type"] == "click"

        print("Visual-DOM mapping test passed.")


if __name__ == "__main__":
    main()