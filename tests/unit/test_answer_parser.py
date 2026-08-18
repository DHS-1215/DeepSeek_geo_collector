import asyncio

import pytest

from app.core.exceptions import AnswerEmptyError
from app.deepseek.answer_parser import (
    AnswerParseResult,
    parse_answer,
)


class _FakeAnswerLocator:
    def __init__(
            self,
            *,
            raw_text: str,
            clean_text: str,
            citation_count: int,
    ) -> None:
        self._raw_text = raw_text
        self._clean_text = clean_text
        self._citation_count = citation_count

    async def inner_text(self) -> str:
        return self._raw_text

    async def evaluate(
            self,
            expression: str,
            arg: str,
    ) -> dict[str, object]:
        return {
            "clean_text": self._clean_text,
            "citation_count": self._citation_count,
        }


def test_parse_answer_keeps_raw_and_returns_clean_text() -> None:
    locator = _FakeAnswerLocator(
        raw_text=(
            "批准文号为国药准字Z15020795-\n"
            "2\n"
            "-\n"
            "5\n"
            "。"
        ),
        clean_text=(
            "批准文号为国药准字Z15020795。"
        ),
        citation_count=2,
    )

    result = asyncio.run(
        parse_answer(locator)
    )

    assert isinstance(
        result,
        AnswerParseResult,
    )

    assert (
            result.raw_text
            == (
                "批准文号为国药准字Z15020795-\n"
                "2\n"
                "-\n"
                "5\n"
                "。"
            )
    )

    assert (
            result.clean_text
            == "批准文号为国药准字Z15020795。"
    )

    assert result.citation_count == 2


def test_parse_answer_preserves_normal_numbers() -> None:
    locator = _FakeAnswerLocator(
        raw_text=(
            "2003年列为非处方药，"
            "2004年至2017年报告137例。"
        ),
        clean_text=(
            "2003年列为非处方药，"
            "2004年至2017年报告137例。"
        ),
        citation_count=0,
    )

    result = asyncio.run(
        parse_answer(locator)
    )

    assert "2003年" in result.clean_text
    assert "2004年至2017年" in result.clean_text
    assert "137例" in result.clean_text


def test_parse_answer_normalizes_blank_lines() -> None:
    locator = _FakeAnswerLocator(
        raw_text="第一段\n\n第二段",
        clean_text=(
            "第一段\n\n\n\n第二段"
        ),
        citation_count=0,
    )

    result = asyncio.run(
        parse_answer(locator)
    )

    assert (
            result.clean_text
            == "第一段\n\n第二段"
    )


def test_parse_answer_rejects_empty_raw_text() -> None:
    locator = _FakeAnswerLocator(
        raw_text="   ",
        clean_text="",
        citation_count=0,
    )

    with pytest.raises(
            AnswerEmptyError,
            match="assistant message is empty",
    ):
        asyncio.run(
            parse_answer(locator)
        )
