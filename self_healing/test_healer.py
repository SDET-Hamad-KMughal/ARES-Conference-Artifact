"""Smoke test for the ARES proactive locator healer."""

from self_healing.healer import LocatorHealer


def main() -> None:
    original = {
        "tag": "button",
        "text": "Sign in",
        "id": "login-button",
        "name": "login",
        "type": "submit",
        "role": "button",
        "class_name": "btn btn-primary",
        "aria_label": "Sign in",
        "placeholder": "",
        "href": "",
        "xpath": "/html/body/form/button[1]",
        "css_selector": "#login-button",
        "x": 500,
        "y": 300,
        "width": 120,
        "height": 40,
    }

    similar_candidate = {
        "tag": "button",
        "text": "Log in",
        "id": "signin-button",
        "name": "login",
        "type": "submit",
        "role": "button",
        "class_name": "btn primary-button",
        "aria_label": "Log in",
        "placeholder": "",
        "href": "",
        "xpath": "/html/body/main/form/button[1]",
        "css_selector": "#signin-button",
        "x": 515,
        "y": 310,
        "width": 125,
        "height": 42,
    }

    unrelated_candidate = {
        "tag": "a",
        "text": "Contact support",
        "id": "support-link",
        "name": "",
        "type": "",
        "role": "link",
        "class_name": "footer-link",
        "aria_label": "Contact support",
        "placeholder": "",
        "href": "/support",
        "xpath": "/html/body/footer/a[3]",
        "css_selector": "#support-link",
        "x": 60,
        "y": 750,
        "width": 150,
        "height": 25,
    }

    healer = LocatorHealer(threshold=0.7)

    result = healer.heal(
        original_element=original,
        candidates=[
            unrelated_candidate,
            similar_candidate,
        ],
        viewport_width=1440,
        viewport_height=900,
    )

    print("Healed:", result.healed)
    print("Selected score:", result.selected_score)
    print("Replacement locator:", result.replacement_locator)
    print("Reason:", result.reason)

    print("\nCandidate ranking")

    for index, ranking in enumerate(
        result.rankings,
        start=1,
    ):
        print(
            {
                "rank": index,
                "text": ranking.candidate.get("text"),
                "textual": ranking.textual_similarity,
                "structural": ranking.structural_similarity,
                "spatial": ranking.spatial_similarity,
                "total": ranking.total_similarity,
                "accepted": ranking.accepted,
            }
        )

    assert result.healed is True
    assert result.selected_candidate is not None
    assert result.selected_candidate["id"] == "signin-button"
    assert result.replacement_locator == {
        "strategy": "id",
        "value": "signin-button",
    }

    assert (
        result.rankings[0].total_similarity
        > result.rankings[1].total_similarity
    )

    print("\nLocator-healing test passed.")


if __name__ == "__main__":
    main()