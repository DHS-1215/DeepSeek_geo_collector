import asyncio

import pytest

import app.deepseek.answer_waiter as answer_waiter_module
from app.core.exceptions import (
    AnswerEmptyError,
    AnswerTimeoutError,
)
from app.deepseek.answer_waiter import wait_for_new_answer


class _FakeAnswerLocator:
    def __init__(
            self,
            texts: list[str],
            *,
            count: int = 1,
    ) -> None:
        self._texts = iter(texts)
        self._current = ""
        self._count = count

    async def count(self) -> int:
        return self._count

    @property
    def last(self) -> "_FakeAnswerLocator":
        return self

    async def inner_text(self) -> str:
        try:
            self._current = next(self._texts)
        except StopIteration:
            pass

        return self._current


class _FakePage:
    def __init__(
            self,
            locator: _FakeAnswerLocator,
    ) -> None:
        self._locator = locator

    def locator(
            self,
            selector: str,
    ) -> _FakeAnswerLocator:
        return self._locator


def test_wait_for_new_answer_returns_after_text_stabilizes(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    times = iter(
        [
            0.0,
            0.1,
            0.2,
            0.8,
        ]
    )

    monkeypatch.setattr(
        answer_waiter_module,
        "monotonic",
        lambda: next(times),
    )

    async def fake_sleep(
            seconds: float,
    ) -> None:
        return None

    monkeypatch.setattr(
        answer_waiter_module.asyncio,
        "sleep",
        fake_sleep,
    )

    page = _FakePage(
        _FakeAnswerLocator(
            [
                "第一段",
                "第一段第二段",
                "第一段第二段",
            ]
        )
    )

    result = asyncio.run(
        wait_for_new_answer(
            page,
            previous_answer_count=0,
            timeout_seconds=10,
            poll_interval_seconds=0.1,
            stable_seconds=0.5,
        )
    )

    assert result.text == "第一段第二段"
    assert result.answer_count == 1
    assert result.elapsed_seconds == 0.8


def test_wait_for_new_answer_raises_timeout(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    times = iter(
        [
            0.0,
            1.0,
        ]
    )

    monkeypatch.setattr(
        answer_waiter_module,
        "monotonic",
        lambda: next(times),
    )

    page = _FakePage(
        _FakeAnswerLocator(
            [],
            count=0,
        )
    )

    with pytest.raises(
            AnswerTimeoutError,
            match="Timed out",
    ):
        asyncio.run(
            wait_for_new_answer(
                page,
                previous_answer_count=0,
                timeout_seconds=0.5,
            )
        )


def test_wait_for_new_answer_raises_when_new_answer_stays_empty(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    times = iter(
        [
            0.0,
            0.1,
            1.0,
        ]
    )

    monkeypatch.setattr(
        answer_waiter_module,
        "monotonic",
        lambda: next(times),
    )

    async def fake_sleep(
            seconds: float,
    ) -> None:
        return None

    monkeypatch.setattr(
        answer_waiter_module.asyncio,
        "sleep",
        fake_sleep,
    )

    page = _FakePage(
        _FakeAnswerLocator(
            [""]
        )
    )

    with pytest.raises(
            AnswerEmptyError,
            match="remained empty",
    ):
        asyncio.run(
            wait_for_new_answer(
                page,
                previous_answer_count=0,
                timeout_seconds=0.5,
            )
        )
