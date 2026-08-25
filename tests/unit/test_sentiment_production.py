import asyncio

from app.analysis.mention import (
    analyze_mentions,
)
from app.analysis.models import (
    MentionTarget,
    ModelResponse,
    SentimentLabel,
    SentimentStatus,
)
from app.analysis.sentiment import (
    analyze_sentiment_with_provider,
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


class FakeProvider:
    provider_name = "fake-provider"
    model_name = "fake-model"

    def __init__(
            self,
            payload: dict,
    ) -> None:
        self.payload = payload
        self.call_count = 0

    async def classify(
            self,
            *,
            system_prompt: str,
            user_prompt: str,
    ) -> ModelResponse:
        self.call_count += 1

        return ModelResponse(
            payload=dict(
                self.payload
            ),
            latency_seconds=0.5,
            prompt_tokens=100,
            completion_tokens=20,
            total_tokens=120,
            raw_content="fake response",
            response_json_keys=list(
                self.payload.keys()
            ),
        )

    async def health_check(
            self,
    ) -> bool:
        return True


class ErrorProvider:
    provider_name = "error-provider"
    model_name = "error-model"

    def __init__(
            self,
            *,
            error_type: str,
    ) -> None:
        self.error_type = (
            error_type
        )

    async def classify(
            self,
            *,
            system_prompt: str,
            user_prompt: str,
    ) -> ModelResponse:
        raise SentimentApiError(
            "provider failed",
            error_type=(
                self.error_type
            ),
        )

    async def health_check(
            self,
    ) -> bool:
        return False


def _target() -> MentionTarget:
    return MentionTarget(
        target_id="hongmao_yaojiu",
        name="鸿茅药酒",
        aliases=[
            "鸿茅药酒",
        ],
    )


def _result(
        answer: str,
) -> GeoRunResult:
    return GeoRunResult(
        provider="deepseek",

        run_id="run_test",

        task=GeoTask(
            task_id="Q001_quick",
            question_id="Q001",
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


def _mention(
        result: GeoRunResult,
):
    return analyze_mentions(
        result=result,
        targets=[
            _target()
        ],
    )


def test_production_sentiment_success() -> None:
    result = _result(
        "鸿茅药酒属于正规药品。"
    )

    provider = FakeProvider(
        {
            "target_name": "鸿茅药酒",
            "sentiment": "neutral",
            "reason": "客观事实描述",
            "evidence": [
                "鸿茅药酒属于正规药品"
            ],
            "confidence": 0.9,
        }
    )

    sentiment = asyncio.run(
        analyze_sentiment_with_provider(
            result=result,
            mention=_mention(result),
            target=_target(),
            provider=provider,
            config=SentimentConfig(),
        )
    )

    assert (
            sentiment.status
            == SentimentStatus.SUCCESS
    )

    assert (
            sentiment.model_sentiment
            == SentimentLabel.NEUTRAL
    )

    assert (
            sentiment.final_sentiment
            == SentimentLabel.NEUTRAL
    )

    assert (
            sentiment.provider
            == "fake-provider"
    )

    assert (
            sentiment.model_name
            == "fake-model"
    )

    assert (
            sentiment.confidence
            == 0.9
    )

    assert sentiment.request_count == 1

    assert provider.call_count == 1


def test_production_sentiment_warning_status() -> None:
    result = _result(
        "鸿茅药酒属于药品。"
    )

    provider = FakeProvider(
        {
            "sentiment": "neutral",
        }
    )

    sentiment = asyncio.run(
        analyze_sentiment_with_provider(
            result=result,
            mention=_mention(result),
            target=_target(),
            provider=provider,
            config=SentimentConfig(),
        )
    )

    assert (
            sentiment.status
            == SentimentStatus
            .SUCCESS_WITH_WARNINGS
    )

    assert sentiment.warnings


def test_invalid_model_payload_fails() -> None:
    result = _result(
        "鸿茅药酒属于药品。"
    )

    provider = FakeProvider(
        {
            "sentiment": "mixed",
        }
    )

    sentiment = asyncio.run(
        analyze_sentiment_with_provider(
            result=result,
            mention=_mention(result),
            target=_target(),
            provider=provider,
            config=SentimentConfig(),
        )
    )

    assert (
            sentiment.status
            == SentimentStatus.FAILED
    )

    assert (
            sentiment.error_type
            == "validation_error"
    )

    assert (
            sentiment.final_sentiment
            is None
    )


def test_negative_priority_overrides_model() -> None:
    result = _result(
        "鸿茅药酒不建议购买。"
    )

    provider = FakeProvider(
        {
            "target_name": "鸿茅药酒",
            "sentiment": "positive",
            "reason": "模型认为正向",
            "evidence": [],
            "confidence": 0.8,
        }
    )

    sentiment = asyncio.run(
        analyze_sentiment_with_provider(
            result=result,
            mention=_mention(result),
            target=_target(),
            provider=provider,
            config=SentimentConfig(),
        )
    )

    assert (
            sentiment.model_sentiment
            == SentimentLabel.POSITIVE
    )

    assert (
            sentiment.final_sentiment
            == SentimentLabel.NEGATIVE
    )

    assert sentiment.rule_hit is True

    assert sentiment.rule_override is True

    assert sentiment.override_applied is True

    assert (
            "NEG_DISCOURAGE_PURCHASE"
            in sentiment.override_rule_codes
    )


def test_tan_qindong_overrides_model() -> None:
    result = _result(
        "鸿茅药酒相关内容提到谭秦东。"
    )

    provider = FakeProvider(
        {
            "target_name": "鸿茅药酒",
            "sentiment": "neutral",
            "reason": "模型中性",
            "evidence": [],
            "confidence": 0.7,
        }
    )

    sentiment = asyncio.run(
        analyze_sentiment_with_provider(
            result=result,
            mention=_mention(result),
            target=_target(),
            provider=provider,
            config=SentimentConfig(),
        )
    )

    assert (
            sentiment.final_sentiment
            == SentimentLabel.NEGATIVE
    )

    assert (
            "NEG_TAN_QINDONG_MENTION"
            in sentiment.override_rule_codes
    )


def test_negated_hongmao_fact_not_overridden() -> None:
    result = _result(
        "鸿茅药酒不存在虚假宣传问题。"
    )

    provider = FakeProvider(
        {
            "target_name": "鸿茅药酒",
            "sentiment": "neutral",
            "reason": "否定负面事实",
            "evidence": [],
            "confidence": 0.9,
        }
    )

    sentiment = asyncio.run(
        analyze_sentiment_with_provider(
            result=result,
            mention=_mention(result),
            target=_target(),
            provider=provider,
            config=SentimentConfig(),
        )
    )

    assert (
            sentiment.final_sentiment
            == SentimentLabel.NEUTRAL
    )

    assert (
            sentiment.rule_override
            is False
    )

    assert (
        sentiment.suppressed_rule_candidates
    )


def test_rate_limit_maps_to_status() -> None:
    result = _result(
        "鸿茅药酒属于药品。"
    )

    sentiment = asyncio.run(
        analyze_sentiment_with_provider(
            result=result,
            mention=_mention(result),
            target=_target(),
            provider=ErrorProvider(
                error_type="rate_limit"
            ),
            config=SentimentConfig(),
        )
    )

    assert (
            sentiment.status
            == SentimentStatus.RATE_LIMITED
    )

    assert (
            sentiment.error_type
            == "rate_limit"
    )


def test_timeout_maps_to_status() -> None:
    result = _result(
        "鸿茅药酒属于药品。"
    )

    sentiment = asyncio.run(
        analyze_sentiment_with_provider(
            result=result,
            mention=_mention(result),
            target=_target(),
            provider=ErrorProvider(
                error_type="timeout"
            ),
            config=SentimentConfig(),
        )
    )

    assert (
            sentiment.status
            == SentimentStatus.TIMEOUT
    )


def test_not_mentioned_skips_provider() -> None:
    result = _result(
        "这是一段普通回答。"
    )

    provider = FakeProvider(
        {
            "sentiment": "positive",
        }
    )

    sentiment = asyncio.run(
        analyze_sentiment_with_provider(
            result=result,
            mention=_mention(result),
            target=_target(),
            provider=provider,
            config=SentimentConfig(),
        )
    )

    assert (
            sentiment.status
            == SentimentStatus.NOT_APPLICABLE
    )

    assert provider.call_count == 0
