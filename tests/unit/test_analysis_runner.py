import asyncio

from unittest.mock import (
    AsyncMock,
    Mock,
)

from app.analysis.models import (
    ModelResponse,
)
from app.core.enums import (
    TaskStatus,
    ValidationStatus,
)
from app.core.models import (
    GeoRunResult,
    GeoTask,
    ValidationResult,
)

import pytest

import app.analysis.runner as analysis_runner_module

from app.analysis.models import (
    MentionBatchResult,
    MentionTarget,
    SentimentBatchResult,
    SentimentStatus,
    SourceTop10Summary,
)
from app.analysis.sentiment_config import (
    SentimentConfig,
)
from app.core.enums import GeoMode


class FakeProvider:
    provider_name = "fake-provider"
    model_name = "fake-model"

    async def classify(
            self,
            *,
            system_prompt: str,
            user_prompt: str,
    ):
        raise AssertionError(
            "provider should be mocked "
            "through batch analyzer"
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


def test_run_geo_analysis_orchestrates_all_layers(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    results = [
        object(),
        object(),
    ]

    targets = [
        _target()
    ]

    mention_result = (
        MentionBatchResult()
    )

    sentiment_result = (
        SentimentBatchResult()
    )

    source_result = (
        SourceTop10Summary(
            total_occurrences=20,
            top10_occurrences=15,
            top10_share=0.75,
            outside_top10_occurrences=5,
            outside_top10_share=0.25,
        )
    )

    mention_mock = Mock(
        return_value=mention_result
    )

    sentiment_mock = AsyncMock(
        return_value=sentiment_result
    )

    source_mock = Mock(
        return_value=source_result
    )

    monkeypatch.setattr(
        analysis_runner_module,
        "analyze_batch_mentions",
        mention_mock,
    )

    monkeypatch.setattr(
        analysis_runner_module,
        (
            "analyze_batch_sentiment_"
            "with_provider"
        ),
        sentiment_mock,
    )

    monkeypatch.setattr(
        analysis_runner_module,
        "analyze_source_top10",
        source_mock,
    )

    provider = FakeProvider()

    config = SentimentConfig()

    analysis = asyncio.run(
        analysis_runner_module
        .run_geo_analysis(
            results=results,
            targets=targets,
            sentiment_provider=provider,
            sentiment_config=config,
        )
    )

    assert (
            analysis.mention
            is mention_result
    )

    assert (
            analysis.sentiment
            is sentiment_result
    )

    assert (
            analysis.sources
            is source_result
    )

    assert (
            analysis.source_mode
            == GeoMode.QUICK
    )

    mention_mock.assert_called_once_with(
        results=results,
        targets=targets,
    )

    sentiment_mock.assert_awaited_once_with(
        results=results,
        mention_batch=mention_result,
        targets=targets,
        provider=provider,
        config=config,
    )

    source_mock.assert_called_once_with(
        results=results,
        mode=GeoMode.QUICK,
    )


def test_run_geo_analysis_supports_explicit_source_mode(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    results = [
        object(),
    ]

    targets = [
        _target()
    ]

    monkeypatch.setattr(
        analysis_runner_module,
        "analyze_batch_mentions",
        Mock(
            return_value=(
                MentionBatchResult()
            )
        ),
    )

    monkeypatch.setattr(
        analysis_runner_module,
        (
            "analyze_batch_sentiment_"
            "with_provider"
        ),
        AsyncMock(
            return_value=(
                SentimentBatchResult()
            )
        ),
    )

    source_mock = Mock(
        return_value=(
            SourceTop10Summary()
        )
    )

    monkeypatch.setattr(
        analysis_runner_module,
        "analyze_source_top10",
        source_mock,
    )

    analysis = asyncio.run(
        analysis_runner_module
        .run_geo_analysis(
            results=results,
            targets=targets,
            sentiment_provider=(
                FakeProvider()
            ),
            sentiment_config=(
                SentimentConfig()
            ),
            source_mode=GeoMode.EXPERT,
        )
    )

    assert (
            analysis.source_mode
            == GeoMode.EXPERT
    )

    source_mock.assert_called_once_with(
        results=results,
        mode=GeoMode.EXPERT,
    )


def test_run_geo_analysis_rejects_empty_targets() -> None:
    with pytest.raises(
            ValueError,
            match=(
                    "analysis targets "
                    "cannot be empty"
            ),
    ):
        asyncio.run(
            analysis_runner_module
            .run_geo_analysis(
                results=[],
                targets=[],
                sentiment_provider=(
                    FakeProvider()
                ),
                sentiment_config=(
                    SentimentConfig()
                ),
            )
        )


class NeutralProvider:
    provider_name = "neutral-provider"
    model_name = "neutral-model"

    async def classify(
            self,
            *,
            system_prompt: str,
            user_prompt: str,
    ) -> ModelResponse:
        payload = {
            "target_name": "鸿茅药酒",
            "sentiment": "neutral",
            "reason": "客观描述",
            "evidence": [],
            "confidence": 0.9,
        }

        return ModelResponse(
            payload=payload,
            latency_seconds=0.01,
            raw_content="test",
            response_json_keys=list(
                payload.keys()
            ),
        )

    async def health_check(
            self,
    ) -> bool:
        return True


def test_run_geo_analysis_real_mention_and_sentiment() -> None:
    run_result = GeoRunResult(
        provider="deepseek",

        run_id="run_test",

        task=GeoTask(
            task_id="Q001_quick",
            question_id="Q001",
            question="测试问题",
            mode=GeoMode.QUICK,
        ),

        answer_text_raw=(
            "鸿茅药酒属于正规药品。"
        ),

        answer_text_clean=(
            "鸿茅药酒属于正规药品。"
        ),

        validation=ValidationResult(
            status=ValidationStatus.PASS,
            is_complete=True,
        ),

        status=TaskStatus.SUCCESS,
    )

    analysis = asyncio.run(
        analysis_runner_module
        .run_geo_analysis(
            results=[
                run_result
            ],
            targets=[
                _target()
            ],
            sentiment_provider=(
                NeutralProvider()
            ),
            sentiment_config=(
                SentimentConfig(
                    max_retries=0,
                )
            ),
        )
    )

    mention_summary = (
        analysis
        .mention
        .summaries[
            "hongmao_yaojiu"
        ]
        .quick
    )

    sentiment_summary = (
        analysis
        .sentiment
        .summaries[
            "hongmao_yaojiu"
        ]
        .quick
    )

    assert (
            mention_summary.valid_count
            == 1
    )

    assert (
            mention_summary.mentioned_count
            == 1
    )

    assert (
            mention_summary.mention_rate
            == 1.0
    )

    assert (
            sentiment_summary
            .classified_mention_count
            == 1
    )

    assert (
            sentiment_summary.neutral_count
            == 1
    )

    assert (
            sentiment_summary
            .non_negative_rate
            == 1.0
    )

    # 默认 GeoRunResult 没有 Sources，
    # 所以 Source Top10 应安全返回零值。
    assert (
            analysis.sources
            .total_occurrences
            == 0
    )

    assert (
            analysis.sources
            .top10_share
            == 0.0
    )



class UnavailableProvider:
    provider_name = "ollama"
    model_name = "qwen2.5:7b"

    def __init__(self) -> None:
        self.health_check_calls = 0
        self.classify_calls = 0

    async def health_check(
            self,
    ) -> bool:
        self.health_check_calls += 1
        return False

    async def classify(
            self,
            *,
            system_prompt: str,
            user_prompt: str,
    ):
        self.classify_calls += 1

        raise AssertionError(
            "classify must not be called"
        )


def test_run_geo_analysis_continues_when_sentiment_provider_unavailable(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_result = GeoRunResult(
        provider="deepseek",

        run_id="run_unavailable",

        task=GeoTask(
            task_id="Q001_quick",
            question_id="Q001",
            question="test question",
            mode=GeoMode.QUICK,
        ),

        answer_text_raw=(
            "\u9e3f\u8305\u836f\u9152"
            "\u88ab\u63d0\u53ca\u3002"
        ),

        answer_text_clean=(
            "\u9e3f\u8305\u836f\u9152"
            "\u88ab\u63d0\u53ca\u3002"
        ),

        validation=ValidationResult(
            status=ValidationStatus.PASS,
            is_complete=True,
        ),

        status=TaskStatus.SUCCESS,
    )

    provider = UnavailableProvider()

    source_result = SourceTop10Summary(
        total_occurrences=10,
        top10_occurrences=6,
        top10_share=0.6,
        outside_top10_occurrences=4,
        outside_top10_share=0.4,
    )

    source_mock = Mock(
        return_value=source_result
    )

    monkeypatch.setattr(
        analysis_runner_module,
        "analyze_source_top10",
        source_mock,
    )

    analysis = asyncio.run(
        analysis_runner_module
        .run_geo_analysis(
            results=[
                run_result
            ],
            targets=[
                _target()
            ],
            sentiment_provider=provider,
            sentiment_config=(
                SentimentConfig()
            ),
        )
    )

    assert (
        provider.health_check_calls
        == 1
    )

    assert (
        provider.classify_calls
        == 0
    )

    sentiment = (
        analysis
        .sentiment
        .details[
            "Q001_quick"
        ][
            "hongmao_yaojiu"
        ]
    )

    assert (
        sentiment.status
        == SentimentStatus.FAILED
    )

    assert (
        sentiment.error_type
        == "provider_unavailable"
    )

    assert (
        analysis.sources
        is source_result
    )

    source_mock.assert_called_once_with(
        results=[
            run_result
        ],
        mode=GeoMode.QUICK,
    )

    summary = (
        analysis
        .sentiment
        .summaries[
            "hongmao_yaojiu"
        ]
        .quick
    )

    assert (
        summary.planned_mention_count
        == 1
    )

    assert (
        summary.classified_mention_count
        == 0
    )

    assert (
        summary.classification_failed_count
        == 1
    )
