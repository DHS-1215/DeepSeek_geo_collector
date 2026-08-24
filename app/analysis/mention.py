import re
import unicodedata

from app.analysis.models import (
    MentionResult,
    MentionTarget,
    TargetMentionResult,
)

from app.analysis.validity import (
    is_valid_analysis_answer,
)
from app.core.models import GeoRunResult


def normalize_text(
        value: str,
) -> str:
    """
    统一提及分析文本格式。

    规则与豆包 GEO 提及分析思想保持一致：
    - Unicode NFKC
    - 转小写
    - 全角空格统一
    - 连续空白归一化
    """

    text = unicodedata.normalize(
        "NFKC",
        value or "",
    )

    text = text.replace(
        "\u3000",
        " ",
    )

    text = text.lower()

    return " ".join(
        text.split()
    )


def analyze_target(
        *,
        answer_text: str,
        target: MentionTarget,
) -> TargetMentionResult:
    """
    分析单个目标在回答正文中的提及情况。
    """

    normalized_answer = normalize_text(
        answer_text
    )

    matched_terms: list[str] = []

    mention_count = 0

    seen_aliases: set[str] = set()

    for alias in target.aliases:
        normalized_alias = normalize_text(
            alias
        )

        if not normalized_alias:
            continue

        if normalized_alias in seen_aliases:
            continue

        seen_aliases.add(
            normalized_alias
        )

        pattern = _alias_pattern(
            normalized_alias
        )

        matches = list(
            re.finditer(
                pattern,
                normalized_answer,
            )
        )

        if not matches:
            continue

        mention_count += len(matches)

        matched_terms.append(
            alias
        )

    return TargetMentionResult(
        target_id=target.target_id,
        mention_count=mention_count,
        matched_terms=matched_terms,
    )


def analyze_mentions(
        *,
        result: GeoRunResult,
        targets: list[MentionTarget],
) -> MentionResult:
    """
    对一条 GeoRunResult 执行目标提及分析。
    """

    is_valid_answer = (
        is_valid_analysis_answer(
            result
        )
    )

    if not is_valid_answer:
        return MentionResult(
            is_valid_answer=False,
        )

    target_results: dict[
        str,
        TargetMentionResult,
    ] = {}

    mentioned_target_ids: list[str] = []

    for target in targets:
        target_result = analyze_target(
            answer_text=(
                result.answer_text_clean
            ),
            target=target,
        )

        target_results[
            target.target_id
        ] = target_result

        if target_result.mention_count > 0:
            mentioned_target_ids.append(
                target.target_id
            )

    return MentionResult(
        is_valid_answer=True,

        mention_any=bool(
            mentioned_target_ids
        ),

        mentioned_target_ids=(
            mentioned_target_ids
        ),

        target_results=target_results,
    )


def _alias_pattern(
        alias: str,
) -> re.Pattern[str]:
    """
    构造允许字符间存在空白的严格 alias 正则。

    例如：

    鸿茅药酒

    可以匹配：

    鸿茅药酒
    鸿 茅 药 酒
    鸿茅 药酒
    """

    compact = re.sub(
        r"\s+",
        "",
        alias,
    )

    pattern = r"\s*".join(
        re.escape(char)
        for char in compact
    )

    return re.compile(
        pattern
    )
