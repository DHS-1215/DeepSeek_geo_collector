import asyncio

from app.analysis.mention_aggregator import (
    analyze_batch_mentions,
)
from app.analysis.models import (
    MentionTarget,
    ModelResponse,
    SentimentLabel,
    SentimentStatus,
)
from app.analysis.sentiment_aggregator import (
    analyze_batch_sentiment_with_provider,
)
from app.analysis.sentiment_config import (
    SentimentConfig,
)
from app.analysis.sentiment_providers import (
    SentimentApiError,
)
from app.core.enums import (
    GeoMode,
    TaskStatus,
    ValidationStatus,
)
from app.core.models import (
    GeoRunResult,
    GeoTask,
    ValidationResult,
)


class MappingProvider:
    provider_name = "mapping-provider"
    model_name = "mapping-model"

    def __init__(self) -> None:
        self.call_count = 0

    async def classify(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> ModelResponse:
        self.call_count += 1

        if "正向样本" in user_prompt:
            label = "positive"

        elif "中性样本" in user_prompt:
            label = "neutral"

        elif "负向样本" in user_prompt:
            label = "negative"

        else:
            raise RuntimeError(
                "unknown test sample"
            )

        payload = {
            "target_name": "鸿茅药酒",
            "sentiment": label,
            "reason": "测试分类",
            "evidence": [],
            "confidence": 0.9,
        }

        return ModelResponse(
            payload=payload,
            latency_seconds=0.1,
            raw_content="test",
            response_json_keys=list(
                payload.keys()
            ),
        )

    async def health_check(
        self,
    ) -> bool:
        return True


class SequenceProvider:
    provider_name = "sequence-provider"
    model_name = "sequence-model"

    def __init__(
        self,
        sequence: list,
    ) -> None:
        self.sequence = list(
            sequence
        )
        self.call_count = 0

    async def classify(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> ModelResponse:
        self.call_count += 1

        item = self.sequence.pop(0)

        if isinstance(
            item,
            Exception,
        ):
            raise item

        return ModelResponse(
            payload=item,
            latency_seconds=0.1,
            raw_content="test",
            response_json_keys=list(
                item.keys()
            ),
        )

    async def health_check(
        self,
    ) -> bool:
        return True


def _target() -> MentionTarget:
    return MentionTarget(
        target_id="hongmao_yaojiu",
        name="鸿茅药酒",
        aliases=[
            "鸿茅药酒",
        ],
    )


def _result(
    *,
    task_id: str,
    question_id: str,
    answer: str,
) -> GeoRunResult:
    return GeoRunResult(
        provider="deepseek",
        run_id=f"run_{task_id}",

        task=GeoTask(
            task_id=task_id,
            question_id=question_id,
            question="测试问题",
            mode=GeoMode.QUICK,
        ),

        answer_text_raw=answer,
        answer_text_clean=answer,

        validation=ValidationResult(
            status=ValidationStatus.PASS,
            is_complete=True,
        ),

        status=TaskStatus.SUCCESS,
    )


def _config() -> SentimentConfig:
    return SentimentConfig(
        max_retries=2,
        retry_backoff_seconds=(
            0,
            0,
        ),
    )


def test_production_batch_non_negative_rate() -> None:
    results = [
        _result(
            task_id="Q001_quick",
            question_id="Q001",
            answer=(
                "鸿茅药酒正向样本。"
            ),
        ),
        _result(
            task_id="Q002_quick",
            question_id="Q002",
            answer=(
                "鸿茅药酒中性样本。"
            ),
        ),
        _result(
            task_id="Q003_quick",
            question_id="Q003",
            answer=(
                "鸿茅药酒负向样本。"
            ),
        ),
    ]

    targets = [
        _target()
    ]

    mention_batch = (
        analyze_batch_mentions(
            results=results,
            targets=targets,
        )
    )

    batch = asyncio.run(
        analyze_batch_sentiment_with_provider(
            results=results,
            mention_batch=mention_batch,
            targets=targets,
            provider=MappingProvider(),
            config=_config(),
        )
    )

    summary = batch.summaries[
        "hongmao_yaojiu"
    ].quick

    assert (
        summary.classified_mention_count
        == 3
    )

    assert summary.positive_count == 1
    assert summary.neutral_count == 1
    assert summary.negative_count == 1

    assert (
        summary.non_negative_rate
        == 2 / 3
    )


def test_retry_then_success() -> None:
    result = _result(
        task_id="Q001_quick",
        question_id="Q001",
        answer="鸿茅药酒普通描述。",
    )

    provider = SequenceProvider(
        [
            SentimentApiError(
                "rate limited",
                error_type="rate_limit",
            ),
            {
                "target_name": "鸿茅药酒",
                "sentiment": "neutral",
                "reason": "测试",
                "evidence": [],
                "confidence": 0.8,
            },
        ]
    )

    targets = [
        _target()
    ]

    mention_batch = (
        analyze_batch_mentions(
            results=[result],
            targets=targets,
        )
    )

    batch = asyncio.run(
        analyze_batch_sentiment_with_provider(
            results=[result],
            mention_batch=mention_batch,
            targets=targets,
            provider=provider,
            config=_config(),
        )
    )

    sentiment = batch.details[
        "Q001_quick"
    ][
        "hongmao_yaojiu"
    ]

    assert provider.call_count == 2

    assert (
        sentiment.status
        == SentimentStatus.SUCCESS
    )

    assert sentiment.attempt_count == 2
    assert sentiment.request_count == 2

    assert (
        sentiment.final_sentiment
        == SentimentLabel.NEUTRAL
    )


def test_retry_exhausted() -> None:
    result = _result(
        task_id="Q001_quick",
        question_id="Q001",
        answer="鸿茅药酒普通描述。",
    )

    provider = SequenceProvider(
        [
            SentimentApiError(
                "timeout 1",
                error_type="timeout",
            ),
            SentimentApiError(
                "timeout 2",
                error_type="timeout",
            ),
            SentimentApiError(
                "timeout 3",
                error_type="timeout",
            ),
        ]
    )

    targets = [
        _target()
    ]

    mention_batch = (
        analyze_batch_mentions(
            results=[result],
            targets=targets,
        )
    )

    batch = asyncio.run(
        analyze_batch_sentiment_with_provider(
            results=[result],
            mention_batch=mention_batch,
            targets=targets,
            provider=provider,
            config=_config(),
        )
    )

    sentiment = batch.details[
        "Q001_quick"
    ][
        "hongmao_yaojiu"
    ]

    assert provider.call_count == 3

    assert (
        sentiment.status
        == SentimentStatus.TIMEOUT
    )

    assert sentiment.attempt_count == 3
    assert sentiment.request_count == 3

    summary = batch.summaries[
        "hongmao_yaojiu"
    ].quick

    assert (
        summary.classified_mention_count
        == 0
    )

    assert (
        summary.classification_failed_count
        == 1
    )


def test_validation_error_does_not_retry() -> None:
    result = _result(
        task_id="Q001_quick",
        question_id="Q001",
        answer="鸿茅药酒普通描述。",
    )

    provider = SequenceProvider(
        [
            {
                "target_name": "鸿茅药酒",
                "sentiment": "mixed",
                "reason": "非法标签",
                "evidence": [],
                "confidence": 0.8,
            },
        ]
    )

    targets = [
        _target()
    ]

    mention_batch = (
        analyze_batch_mentions(
            results=[result],
            targets=targets,
        )
    )

    batch = asyncio.run(
        analyze_batch_sentiment_with_provider(
            results=[result],
            mention_batch=mention_batch,
            targets=targets,
            provider=provider,
            config=_config(),
        )
    )

    sentiment = batch.details[
        "Q001_quick"
    ][
        "hongmao_yaojiu"
    ]

    assert provider.call_count == 1

    assert (
        sentiment.error_type
        == "validation_error"
    )

    assert sentiment.attempt_count == 1
    assert sentiment.request_count == 1