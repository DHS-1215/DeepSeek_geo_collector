from app.analysis.models import (
    MentionTarget,
)
from app.analysis.sentiment_context import (
    extract_target_context,
    split_sentences,
)


def _target() -> MentionTarget:
    return MentionTarget(
        target_id="hongmao_yaojiu",
        name="鸿茅药酒",
        aliases=[
            "鸿茅药酒",
        ],
    )


def test_split_sentences() -> None:
    sentences = split_sentences(
        "第一句。第二句！第三句？"
    )

    assert len(sentences) == 3

    assert (
            sentences[0].text
            == "第一句。"
    )


def test_extract_context_without_hit() -> None:
    context = extract_target_context(
        answer_text=(
            "这是一段普通回答。"
        ),
        target=_target(),
    )

    assert (
            context.target_context
            == ""
    )

    assert (
            context.matched_aliases
            == []
    )


def test_extract_target_context() -> None:
    answer = (
        "第一句。"
        "第二句。"
        "鸿茅药酒属于药品。"
        "第四句。"
        "第五句。"
        "第六句。"
    )

    context = extract_target_context(
        answer_text=answer,
        target=_target(),
    )

    assert (
            "鸿茅药酒属于药品。"
            in context.target_context
    )

    assert (
            context.matched_aliases
            == ["鸿茅药酒"]
    )

    assert (
            len(context.context_spans)
            >= 1
    )


def test_context_keeps_two_sentences_before_and_after() -> None:
    answer = (
        "A。"
        "B。"
        "鸿茅药酒。"
        "D。"
        "E。"
        "F。"
    )

    context = extract_target_context(
        answer_text=answer,
        target=_target(),
    )

    assert "A。" in context.target_context
    assert "B。" in context.target_context
    assert "D。" in context.target_context
    assert "E。" in context.target_context

    assert "F。" not in context.target_context


def test_related_conclusion_sentence_is_added() -> None:
    answer = (
        "鸿茅药酒是一种药品。"
        "中间普通句。"
        "再一条普通句。"
        "继续普通句。"
        "鸿茅药酒是否值得购买需要结合个人情况。"
    )

    context = extract_target_context(
        answer_text=answer,
        target=_target(),
        sentences_before=0,
        sentences_after=0,
    )

    assert (
            "鸿茅药酒是否值得购买需要结合个人情况。"
            in context.target_context
    )
