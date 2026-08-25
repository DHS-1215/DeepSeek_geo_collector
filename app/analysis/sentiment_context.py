from __future__ import annotations

import re
from dataclasses import dataclass

from app.analysis.mention import normalize_text
from app.analysis.models import (
    MentionTarget,
    TargetContext,
)

CONCLUSION_KEYWORDS = [
    "建议",
    "推荐",
    "不建议",
    "不推荐",
    "风险",
    "争议",
    "值得",
    "可靠",
    "不可靠",
    "购买",
    "使用",
    "选择",
    "结论",
]


@dataclass(frozen=True)
class SentenceSpan:
    text: str
    start: int
    end: int


def extract_target_context(
        *,
        answer_text: str,
        target: MentionTarget,
        sentences_before: int = 2,
        sentences_after: int = 2,
) -> TargetContext:
    """
    提取目标产品相关上下文。

    口径沿用豆包：
    - 找到 target aliases 的正文命中
    - 每个命中保留前 2 句、当前句、后 2 句
    - 额外加入包含目标 alias 且含结论关键词的句子
    """

    sentences = split_sentences(
        answer_text
    )

    hits = _find_hits(
        answer_text,
        target.aliases,
    )

    if not hits:
        return TargetContext(
            target_context="",
            matched_aliases=[],
            context_spans=[],
        )

    selected_indexes: set[int] = set()

    spans: list[
        dict[str, int | str]
    ] = []

    matched_aliases: list[str] = []

    for hit in hits:
        alias = str(
            hit["alias"]
        )

        if alias not in matched_aliases:
            matched_aliases.append(
                alias
            )

        sentence_index = (
            _sentence_index_for_position(
                sentences,
                int(hit["start"]),
            )
        )

        if sentence_index is None:
            continue

        start = max(
            0,
            sentence_index - sentences_before,
        )

        end = min(
            len(sentences) - 1,
            sentence_index + sentences_after,
        )

        selected_indexes.update(
            range(start, end + 1)
        )

        spans.append(
            {
                "alias": alias,
                "start": int(
                    hit["start"]
                ),
                "end": int(
                    hit["end"]
                ),
                "sentence_index": (
                    sentence_index
                ),
            }
        )

    selected_indexes.update(
        _related_conclusion_indexes(
            sentences,
            target.aliases,
        )
    )

    ordered_sentences = [
        sentences[index].text.strip()
        for index
        in sorted(selected_indexes)
        if sentences[index].text.strip()
    ]

    return TargetContext(
        target_context="\n".join(
            dict.fromkeys(
                ordered_sentences
            )
        ),
        matched_aliases=(
            matched_aliases
        ),
        context_spans=spans,
    )


def split_sentences(
        text: str,
) -> list[SentenceSpan]:
    spans: list[SentenceSpan] = []

    start = 0

    for match in re.finditer(
            r"[^。！？!?；;\n]+"
            r"[。！？!?；;]?",
            text or "",
    ):
        sentence = (
            match.group(0).strip()
        )

        if not sentence:
            continue

        spans.append(
            SentenceSpan(
                sentence,
                match.start(),
                match.end(),
            )
        )

        start = match.end()

    if not spans and text.strip():
        spans.append(
            SentenceSpan(
                text.strip(),
                start,
                len(text),
            )
        )

    return spans


def _find_hits(
        answer_text: str,
        aliases: list[str],
) -> list[dict[str, int | str]]:
    normalized_answer = normalize_text(
        answer_text
    )

    normalized_aliases = [
        (
            alias,
            normalize_text(alias),
        )
        for alias in aliases
    ]

    hits: list[
        dict[str, int | str]
    ] = []

    for alias, normalized_alias in (
            normalized_aliases
    ):
        if not normalized_alias:
            continue

        pattern = re.compile(
            r"\s*".join(
                re.escape(char)
                for char
                in normalized_alias
            )
        )

        for match in pattern.finditer(
                normalized_answer
        ):
            original = (
                _find_original_span(
                    answer_text,
                    alias,
                )
            )

            if original:
                hits.append(
                    {
                        "alias": alias,
                        "start": original[0],
                        "end": original[1],
                    }
                )

            else:
                hits.append(
                    {
                        "alias": alias,
                        "start": match.start(),
                        "end": match.end(),
                    }
                )

    return sorted(
        hits,
        key=lambda item: int(
            item["start"]
        ),
    )


def _find_original_span(
        answer_text: str,
        alias: str,
) -> tuple[int, int] | None:
    pattern = re.compile(
        r"\s*".join(
            re.escape(char)
            for char in alias
            if not char.isspace()
        )
    )

    match = pattern.search(
        answer_text
    )

    if not match:
        return None

    return (
        match.start(),
        match.end(),
    )


def _sentence_index_for_position(
        sentences: list[SentenceSpan],
        position: int,
) -> int | None:
    for index, sentence in enumerate(
            sentences
    ):
        if (
                sentence.start
                <= position
                < sentence.end
        ):
            return index

    return None


def _related_conclusion_indexes(
        sentences: list[SentenceSpan],
        aliases: list[str],
) -> set[int]:
    indexes: set[int] = set()

    for index, sentence in enumerate(
            sentences
    ):
        text = sentence.text

        if not any(
                alias
                and alias in text
                for alias in aliases
        ):
            continue

        if any(
                keyword in text
                for keyword
                in CONCLUSION_KEYWORDS
        ):
            indexes.add(
                index
            )

    return indexes
