from app.analysis.models import (
    MentionTarget,
)
from app.analysis.sentiment_prompt import (
    OUTPUT_SCHEMA_INSTRUCTION,
    SYSTEM_PROMPT,
    build_user_prompt,
)


def _target() -> MentionTarget:
    return MentionTarget(
        target_id="hongmao_yaojiu",
        name="鸿茅药酒",
        aliases=[
            "鸿茅药酒",
            "鸿茅",
        ],
    )


def test_system_prompt_contains_three_labels() -> None:
    assert "positive" in SYSTEM_PROMPT
    assert "neutral" in SYSTEM_PROMPT
    assert "negative" in SYSTEM_PROMPT


def test_schema_instruction_requires_five_keys() -> None:
    for key in (
            "target_name",
            "sentiment",
            "reason",
            "evidence",
            "confidence",
    ):
        assert (
                key
                in OUTPUT_SCHEMA_INSTRUCTION
        )


def test_build_user_prompt_contains_target() -> None:
    prompt = build_user_prompt(
        target=_target(),
        target_context=(
            "鸿茅药酒属于药品。"
        ),
        full_answer=(
            "鸿茅药酒属于药品。"
        ),
        evidence_max_items=3,
    )

    assert (
            "target_name: 鸿茅药酒"
            in prompt
    )

    assert (
            "鸿茅药酒、鸿茅"
            in prompt
    )


def test_build_user_prompt_contains_context_and_answer() -> None:
    prompt = build_user_prompt(
        target=_target(),
        target_context="目标上下文",
        full_answer="完整回答",
        evidence_max_items=3,
    )

    assert "目标上下文" in prompt
    assert "完整回答" in prompt


def test_full_answer_is_limited_to_10000_chars() -> None:
    long_answer = (
            "A" * 10000
            + "SHOULD_NOT_APPEAR"
    )

    prompt = build_user_prompt(
        target=_target(),
        target_context="context",
        full_answer=long_answer,
        evidence_max_items=3,
    )

    assert (
            "SHOULD_NOT_APPEAR"
            not in prompt
    )
