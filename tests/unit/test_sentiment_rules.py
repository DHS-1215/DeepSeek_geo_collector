from app.analysis.models import (
    MentionTarget,
    SentimentLabel,
    SentimentResult,
    SentimentStatus,
)
from app.analysis.sentiment_rules import (
    NEG_CROSS_PROVINCE_RULE_CODE,
    NEG_TAN_QINDONG_RULE_CODE,
    apply_hongmao_full_answer_negative_facts,
    apply_negative_priority,
    apply_target_specific_overrides,
    finalize_rule_flags,
    is_negated_match,
)


def _hongmao_target() -> MentionTarget:
    return MentionTarget(
        target_id="hongmao_yaojiu",
        name="鸿茅药酒",
        aliases=[
            "鸿茅药酒",
        ],
    )


def _result(
        *,
        model_sentiment: SentimentLabel,
) -> SentimentResult:
    return SentimentResult(
        target_id="hongmao_yaojiu",
        target_name="鸿茅药酒",
        status=SentimentStatus.SUCCESS,
        model_sentiment=model_sentiment,
        final_sentiment=model_sentiment,
    )


def test_negative_priority_detects_discourage_purchase() -> None:
    match = apply_negative_priority(
        "鸿茅药酒不建议购买。",
        target_aliases=[
            "鸿茅药酒",
        ],
    )

    assert match is not None

    assert (
            "NEG_DISCOURAGE_PURCHASE"
            in match["rule_codes"]
    )


def test_negative_priority_ignores_negated_penalty() -> None:
    match = apply_negative_priority(
        "鸿茅药酒并未被监管处罚。",
        target_aliases=[
            "鸿茅药酒",
        ],
    )

    assert match is None


def test_is_negated_match() -> None:
    text = (
        "鸿茅药酒不存在虚假宣传问题。"
    )

    start = text.index(
        "虚假宣传"
    )

    end = (
            start
            + len("虚假宣传")
    )

    result = is_negated_match(
        text,
        start,
        end,
    )

    assert result is not None


def test_tan_qindong_forces_negative() -> None:
    result = _result(
        model_sentiment=(
            SentimentLabel.POSITIVE
        )
    )

    apply_target_specific_overrides(
        result=result,
        target=_hongmao_target(),
        answer_text=(
            "鸿茅药酒相关内容提到谭秦东。"
        ),
        evidence_max_items=3,
    )

    finalize_rule_flags(
        result
    )

    assert (
            result.final_sentiment
            == SentimentLabel.NEGATIVE
    )

    assert (
            NEG_TAN_QINDONG_RULE_CODE
            in result.override_rule_codes
    )

    assert result.rule_hit is True
    assert result.rule_override is True
    assert result.override_applied is True


def test_cross_province_forces_negative() -> None:
    result = _result(
        model_sentiment=(
            SentimentLabel.NEUTRAL
        )
    )

    apply_target_specific_overrides(
        result=result,
        target=_hongmao_target(),
        answer_text=(
            "鸿茅药酒曾出现跨省相关事件。"
        ),
        evidence_max_items=3,
    )

    finalize_rule_flags(
        result
    )

    assert (
            result.final_sentiment
            == SentimentLabel.NEGATIVE
    )

    assert (
            NEG_CROSS_PROVINCE_RULE_CODE
            in result.override_rule_codes
    )


def test_rule_hit_without_override_when_model_already_negative() -> None:
    result = _result(
        model_sentiment=(
            SentimentLabel.NEGATIVE
        )
    )

    apply_target_specific_overrides(
        result=result,
        target=_hongmao_target(),
        answer_text=(
            "鸿茅药酒相关内容提到谭秦东。"
        ),
        evidence_max_items=3,
    )

    finalize_rule_flags(
        result
    )

    assert result.rule_hit is True

    assert result.rule_override is False

    assert result.override_applied is False


def test_hongmao_false_advertising_forces_negative() -> None:
    result = _result(
        model_sentiment=(
            SentimentLabel.NEUTRAL
        )
    )

    apply_hongmao_full_answer_negative_facts(
        result=result,
        target=_hongmao_target(),
        answer_text=(
            "鸿茅药酒曾涉及虚假宣传问题。"
        ),
        evidence_max_items=3,
    )

    finalize_rule_flags(
        result
    )

    assert (
            result.final_sentiment
            == SentimentLabel.NEGATIVE
    )

    assert (
            "NEG_HONGMAO_FALSE_ADVERTISING"
            in result.override_rule_codes
    )


def test_negated_hongmao_fact_is_suppressed() -> None:
    result = _result(
        model_sentiment=(
            SentimentLabel.NEUTRAL
        )
    )

    apply_hongmao_full_answer_negative_facts(
        result=result,
        target=_hongmao_target(),
        answer_text=(
            "鸿茅药酒不存在虚假宣传问题。"
        ),
        evidence_max_items=3,
    )

    finalize_rule_flags(
        result
    )

    assert (
            result.final_sentiment
            == SentimentLabel.NEUTRAL
    )

    assert (
            "NEG_HONGMAO_FALSE_ADVERTISING"
            not in result.override_rule_codes
    )

    assert (
        result.suppressed_rule_candidates
    )


def test_hongmao_rule_requires_hongmao_target() -> None:
    other_target = MentionTarget(
        target_id="other_product",
        name="其他产品",
        aliases=[
            "其他产品",
        ],
    )

    result = SentimentResult(
        target_id="other_product",
        status=SentimentStatus.SUCCESS,
        model_sentiment=(
            SentimentLabel.NEUTRAL
        ),
        final_sentiment=(
            SentimentLabel.NEUTRAL
        ),
    )

    apply_hongmao_full_answer_negative_facts(
        result=result,
        target=other_target,
        answer_text=(
            "其他产品存在虚假宣传。"
        ),
        evidence_max_items=3,
    )

    finalize_rule_flags(
        result
    )

    assert (
            result.final_sentiment
            == SentimentLabel.NEUTRAL
    )

    assert (
            result.override_rule_codes
            == []
    )


def test_rule_evidence_is_added() -> None:
    result = _result(
        model_sentiment=(
            SentimentLabel.POSITIVE
        )
    )

    answer = (
        "鸿茅药酒相关内容提到谭秦东。"
    )

    apply_target_specific_overrides(
        result=result,
        target=_hongmao_target(),
        answer_text=answer,
        evidence_max_items=3,
    )

    assert result.evidence

    assert (
            "谭秦东"
            in result.evidence[-1]
    )
