import pytest

from app.analysis.sentiment_validation import (
    validate_model_payload,
)


def test_valid_payload() -> None:
    payload = {
        "target_name": "鸿茅药酒",
        "sentiment": "positive",
        "reason": "认可产品",
        "evidence": [
            "鸿茅药酒值得选择"
        ],
        "confidence": 0.9,
    }

    normalized, error, warnings, coercion, diagnostics = (
        validate_model_payload(
            payload,
            target_name="鸿茅药酒",
            original_answer=(
                "鸿茅药酒值得选择"
            ),
            evidence_max_items=3,
        )
    )

    assert error is None

    assert (
        normalized["sentiment"]
        == "positive"
    )

    assert (
        normalized["confidence"]
        == 0.9
    )

    assert warnings == []

    assert coercion == {}

    assert (
        diagnostics[
            "confidence_parsed"
        ]
        == 0.9
    )


def test_invalid_sentiment_fails() -> None:
    normalized, error, *_ = (
        validate_model_payload(
            {
                "sentiment": "mixed",
            },
            target_name="鸿茅药酒",
            original_answer="回答",
            evidence_max_items=3,
        )
    )

    assert (
        error
        == "missing or invalid sentiment"
    )


@pytest.mark.parametrize(
    ("legacy_key", "value"),
    [
        ("answer", "positive"),
        ("label", "neutral"),
        ("result", "negative"),
    ],
)
def test_legacy_sentiment_field_is_coerced(
    legacy_key: str,
    value: str,
) -> None:
    normalized, error, warnings, coercion, _ = (
        validate_model_payload(
            {
                legacy_key: value,
            },
            target_name="鸿茅药酒",
            original_answer="回答",
            evidence_max_items=3,
        )
    )

    assert error is None

    assert (
        normalized["sentiment"]
        == value
    )

    assert (
        coercion[
            legacy_key
        ]
        == "sentiment"
    )

    assert (
        f"coerced {legacy_key} to sentiment"
        in warnings
    )


def test_target_name_mismatch_fails() -> None:
    _, error, *_ = (
        validate_model_payload(
            {
                "target_name": "其他产品",
                "sentiment": "neutral",
            },
            target_name="鸿茅药酒",
            original_answer="回答",
            evidence_max_items=3,
        )
    )

    assert (
        error
        == "target_name mismatch"
    )


def test_missing_optional_fields_are_repaired() -> None:
    normalized, error, warnings, _, diagnostics = (
        validate_model_payload(
            {
                "sentiment": "neutral",
            },
            target_name="鸿茅药酒",
            original_answer="回答",
            evidence_max_items=3,
        )
    )

    assert error is None

    assert (
        normalized["target_name"]
        == "鸿茅药酒"
    )

    assert (
        normalized["reason"]
        == "模型未返回原因"
    )

    assert normalized["evidence"] == []

    assert (
        normalized["confidence"]
        is None
    )

    assert warnings

    assert (
        diagnostics[
            "confidence_missing"
        ]
        is True
    )


def test_invalid_evidence_is_removed() -> None:
    normalized, error, warnings, *_ = (
        validate_model_payload(
            {
                "sentiment": "negative",
                "evidence": [
                    "真实证据",
                    "模型编造的证据",
                ],
                "confidence": 0.8,
            },
            target_name="鸿茅药酒",
            original_answer=(
                "这里包含真实证据。"
            ),
            evidence_max_items=3,
        )
    )

    assert error is None

    assert (
        normalized["evidence"]
        == ["真实证据"]
    )

    assert (
        "invalid evidence items removed"
        in warnings
    )


def test_confidence_percentage_is_normalized() -> None:
    normalized, error, warnings, _, diagnostics = (
        validate_model_payload(
            {
                "sentiment": "positive",
                "confidence": "85%",
            },
            target_name="鸿茅药酒",
            original_answer="回答",
            evidence_max_items=3,
        )
    )

    assert error is None

    assert (
        normalized["confidence"]
        == pytest.approx(0.85)
    )

    assert (
        "confidence percentage normalized"
        in warnings
    )

    assert (
        diagnostics[
            "confidence_fallback_applied"
        ]
        is True
    )


@pytest.mark.parametrize(
    "confidence",
    [
        True,
        "很有信心",
        1.5,
        -0.1,
        "150%",
    ],
)
def test_invalid_confidence_is_cleared(
    confidence,
) -> None:
    normalized, error, warnings, _, _ = (
        validate_model_payload(
            {
                "sentiment": "neutral",
                "confidence": confidence,
            },
            target_name="鸿茅药酒",
            original_answer="回答",
            evidence_max_items=3,
        )
    )

    assert error is None

    assert (
        normalized["confidence"]
        is None
    )

    assert warnings
