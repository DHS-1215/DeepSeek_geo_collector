import re
from dataclasses import dataclass

from playwright.async_api import Locator

from app.core.exceptions import AnswerEmptyError
from app.deepseek.selectors import CITATION_MARKER


@dataclass(frozen=True, slots=True)
class AnswerParseResult:
    """DeepSeek 回答解析结果。"""

    raw_text: str
    clean_text: str
    citation_count: int


def _normalize_clean_text(text: str) -> str:
    """对清洗后的正文做最小限度的格式规范化。"""

    text = (
        text
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )

    lines = [
        line.rstrip()
        for line in text.splitlines()
    ]

    text = "\n".join(lines)

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


def normalize_clean_text(text: str) -> str:
    """规范 DeepSeek clean answer 文本。"""

    text = (
        text
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )

    lines = [
        line.rstrip()
        for line in text.splitlines()
    ]

    text = "\n".join(lines)

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


async def parse_answer(
        answer: Locator,
) -> AnswerParseResult:
    """从 assistant 正文 DOM 中提取 raw / clean answer。"""

    raw_text = (
        await answer.inner_text()
    ).strip()

    if not raw_text:
        raise AnswerEmptyError(
            "DeepSeek assistant message is empty."
        )

    dom_result = await answer.evaluate(
        """
        (el, citationSelector) => {
            const clone = el.cloneNode(true);

            const citations = [
                ...clone.querySelectorAll(
                    citationSelector
                )
            ];

            const citationCount =
                citations.length;

            for (const citation of citations) {
                const anchor =
                    citation.closest("a");

                if (
                    anchor &&
                    clone.contains(anchor)
                ) {
                    anchor.remove();
                } else {
                    citation.remove();
                }
            }

            const holder =
                document.createElement("div");

            holder.style.position =
                "fixed";

            holder.style.left =
                "-100000px";

            holder.style.top =
                "0";

            holder.style.width =
                "1000px";

            holder.style.pointerEvents =
                "none";

            holder.appendChild(clone);

            document.body.appendChild(
                holder
            );

            const cleanText =
                clone.innerText || "";

            holder.remove();

            return {
                clean_text: cleanText,
                citation_count: citationCount
            };
        }
        """,
        CITATION_MARKER,
    )

    clean_text = _normalize_clean_text(
        str(
            dom_result.get(
                "clean_text",
                "",
            )
        )
    )

    if not clean_text:
        raise AnswerEmptyError(
            "DeepSeek answer became empty "
            "after citation removal."
        )

    return AnswerParseResult(
        raw_text=raw_text,
        clean_text=clean_text,
        citation_count=int(
            dom_result.get(
                "citation_count",
                0,
            )
        ),
    )
