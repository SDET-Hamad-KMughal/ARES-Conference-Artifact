"""Smoke test for ARES similarity components."""

from self_healing.similarity import SimilarityEngine


def main() -> None:
    engine = SimilarityEngine()

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
        "x": 60,
        "y": 750,
        "width": 150,
        "height": 25,
    }

    similar_scores = engine.calculate_components(
        original,
        similar_candidate,
        viewport_width=1440,
        viewport_height=900,
    )

    unrelated_scores = engine.calculate_components(
        original,
        unrelated_candidate,
        viewport_width=1440,
        viewport_height=900,
    )

    print("Similar candidate:", similar_scores)
    print("Unrelated candidate:", unrelated_scores)

    assert 0.0 <= similar_scores["semantic"] <= 1.0
    assert 0.0 <= similar_scores["structural"] <= 1.0
    assert 0.0 <= similar_scores["spatial"] <= 1.0

    assert (
        similar_scores["structural"]
        > unrelated_scores["structural"]
    )

    assert (
        similar_scores["spatial"]
        > unrelated_scores["spatial"]
    )

    print("Similarity component test passed.")


if __name__ == "__main__":
    main()