from typing import Protocol

from app.analysis.models import (
    MentionResult,
    MentionTarget,
    SentimentLabel,
    SentimentResult,
    SentimentStatus,
)
from app.core.models import GeoRunResult


class SentimentClassifier(Protocol):
    """
    情感分类器接口。

    后续可以接：
    - Ollama
    - 智谱
    - OpenAI Compatible API
    - 测试 Fake Classifier
    """

    async def classify(
            self,
            *,
            answer_text: str,
            target: MentionTarget,
    ) -> SentimentLabel | str:
        ...


def should_classify_sentiment(
        *,
        result: GeoRunResult,
        mention: MentionResult,
        target_id: str,
) -> bool:
    """
    判断一个目标是否需要执行情感分类。

    豆包既有口径：
    - 回答必须有效
    - 回答正文必须非空
    - 当前目标必须被提及
    """

    if not mention.is_valid_answer:
        return False

    if not result.answer_text_clean.strip():
        return False

    target_result = (
        mention.target_results.get(
            target_id
        )
    )

    if target_result is None:
        return False

    return (
            target_result.mention_count
            > 0
    )


async def analyze_sentiment(
        *,
        result: GeoRunResult,
        mention: MentionResult,
        target: MentionTarget,
        classifier: SentimentClassifier,
) -> SentimentResult:
    """
    对一条回答中的单个目标执行情感分析。
    """

    if not should_classify_sentiment(
            result=result,
            mention=mention,
            target_id=target.target_id,
    ):
        return SentimentResult(
            target_id=target.target_id,
            status=(
                SentimentStatus
                .NOT_APPLICABLE
            ),
        )

    try:
        raw_label = await classifier.classify(
            answer_text=(
                result.answer_text_clean
            ),
            target=target,
        )

        label = _normalize_label(
            raw_label
        )

    except Exception as exc:
        return SentimentResult(
            target_id=target.target_id,
            status=SentimentStatus.FAILED,
            reason=str(exc),
            provider=(
                _classifier_name(
                    classifier
                )
            ),
        )

    return SentimentResult(
        target_id=target.target_id,
        status=SentimentStatus.SUCCESS,
        final_sentiment=label,
        provider=(
            _classifier_name(
                classifier
            )
        ),
    )


def _normalize_label(
        value: SentimentLabel | str,
) -> SentimentLabel:
    """
    将分类器输出规范化为标准 SentimentLabel。

    只允许：
    positive
    neutral
    negative
    """

    if isinstance(
            value,
            SentimentLabel,
    ):
        return value

    normalized = (
        str(value)
        .strip()
        .lower()
    )

    try:
        return SentimentLabel(
            normalized
        )

    except ValueError as exc:
        raise ValueError(
            "unsupported sentiment label: "
            f"{value!r}"
        ) from exc


def _classifier_name(
        classifier: SentimentClassifier,
) -> str:
    """
    返回分类器名称，便于结果追踪。
    """

    name = getattr(
        classifier,
        "name",
        None,
    )

    if name:
        return str(name)

    return (
        classifier
        .__class__
        .__name__
    )
