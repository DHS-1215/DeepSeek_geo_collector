import asyncio
from time import monotonic
from dataclasses import dataclass

from playwright.async_api import Page

from app.core.exceptions import (
    AnswerEmptyError,
    AnswerTimeoutError,
)
from app.deepseek.selectors import (
    ASSISTANT_MESSAGE_MAIN,
)


@dataclass(frozen=True, slots=True)
class AnswerWaitResult:
    """回答等待完成后的结果。"""

    text: str
    elapsed_seconds: float
    answer_count: int


async def wait_for_new_answer(
    page: Page,
    *,
    previous_answer_count: int,
    timeout_seconds: int,
    poll_interval_seconds: float = 0.5,
    stable_seconds: float = 5.0,
) -> AnswerWaitResult:
    """等待新的 DeepSeek 回答出现并稳定。"""

    if timeout_seconds <= 0:
        raise ValueError(
            "timeout_seconds must be greater than 0."
        )

    if poll_interval_seconds <= 0:
        raise ValueError(
            "poll_interval_seconds must be greater than 0."
        )

    if stable_seconds <= 0:
        raise ValueError(
            "stable_seconds must be greater than 0."
        )

    started_at = monotonic()

    last_text = ""
    last_changed_at: float | None = None

    saw_new_answer = False

    while True:
        now = monotonic()
        elapsed = now - started_at

        if elapsed >= timeout_seconds:
            break

        answers = page.locator(
            ASSISTANT_MESSAGE_MAIN
        )

        answer_count = await answers.count()

        if answer_count > previous_answer_count:
            saw_new_answer = True

            text = (
                await answers.last.inner_text()
            ).strip()

            if text:
                if text != last_text:
                    last_text = text
                    last_changed_at = now

                elif (
                    last_changed_at is not None
                    and now - last_changed_at
                    >= stable_seconds
                ):
                    return AnswerWaitResult(
                        text=text,
                        elapsed_seconds=round(
                            elapsed,
                            2,
                        ),
                        answer_count=answer_count,
                    )

        await asyncio.sleep(
            poll_interval_seconds
        )

    if saw_new_answer and not last_text:
        raise AnswerEmptyError(
            "DeepSeek created a new assistant message "
            "but the answer text remained empty."
        )

    raise AnswerTimeoutError(
        "Timed out while waiting for DeepSeek "
        f"answer to stabilize after {timeout_seconds} seconds. "
        f"Last answer length: {len(last_text)}."
    )