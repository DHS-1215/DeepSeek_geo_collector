from app.analysis.models import (
    BatchAnalysisSummary,
    MentionResult,
    MentionSummary,
    SentimentLabel,
    SentimentResult,
    SentimentStatus,
    SentimentSummary,
    SourceRankItem,
    SourceTop10Summary,
    TargetMentionResult,
    MentionBatchResult,
    TargetMentionSummary,
    SentimentBatchResult,
    TargetSentimentSummary,
    ModelResponse,
    TargetContext,
    GeoAnalysisResult
)
from app.core.enums import GeoMode


def test_sentiment_label_values() -> None:
    assert (
            SentimentLabel.POSITIVE.value
            == "positive"
    )

    assert (
            SentimentLabel.NEUTRAL.value
            == "neutral"
    )

    assert (
            SentimentLabel.NEGATIVE.value
            == "negative"
    )

    assert (
            SentimentStatus.RATE_LIMITED.value
            == "rate_limited"
    )

    assert (
            SentimentStatus.TIMEOUT.value
            == "timeout"
    )


def test_sentiment_status_values() -> None:
    assert (
            SentimentStatus.SUCCESS.value
            == "success"
    )

    assert (
            SentimentStatus.SUCCESS_WITH_WARNINGS.value
            == "success_with_warnings"
    )

    assert (
            SentimentStatus.FAILED.value
            == "failed"
    )

    assert (
            SentimentStatus.NOT_APPLICABLE.value
            == "not_applicable"
    )


def test_target_mention_result_defaults() -> None:
    result = TargetMentionResult(
        target_id="hongmao_yaojiu"
    )

    assert result.mention_count == 0
    assert result.matched_terms == []


def test_mention_result_supports_target_results() -> None:
    target = TargetMentionResult(
        target_id="hongmao_yaojiu",
        mention_count=2,
        matched_terms=[
            "鸿茅药酒",
        ],
    )

    result = MentionResult(
        is_valid_answer=True,
        mention_any=True,
        mentioned_target_ids=[
            "hongmao_yaojiu",
        ],
        target_results={
            "hongmao_yaojiu": target,
        },
    )

    assert result.is_valid_answer is True
    assert result.mention_any is True

    assert result.mentioned_target_ids == [
        "hongmao_yaojiu"
    ]

    assert (
            result.target_results[
                "hongmao_yaojiu"
            ].mention_count
            == 2
    )


def test_sentiment_result_can_be_not_applicable() -> None:
    result = SentimentResult(
        target_id="hongmao_yaojiu",
        status=(
            SentimentStatus.NOT_APPLICABLE
        ),
    )

    assert result.final_sentiment is None


def test_sentiment_result_can_store_label() -> None:
    result = SentimentResult(
        target_id="hongmao_yaojiu",
        status=SentimentStatus.SUCCESS,
        final_sentiment=(
            SentimentLabel.POSITIVE
        ),
        provider="test-provider",
    )

    assert (
            result.final_sentiment
            == SentimentLabel.POSITIVE
    )

    assert result.provider == "test-provider"


def test_source_rank_item() -> None:
    item = SourceRankItem(
        source_key="https://example.com/a",
        occurrence_count=8,
        question_count=5,
        average_order=2.5,
        first_seen_order=1,
        share=0.2,
        site_name="example",
    )

    assert item.occurrence_count == 8
    assert item.question_count == 5
    assert item.share == 0.2


def test_source_top10_summary_defaults() -> None:
    summary = SourceTop10Summary()

    assert summary.total_occurrences == 0

    assert summary.top10_occurrences == 0

    assert summary.top10_share == 0.0

    assert (
            summary.outside_top10_occurrences
            == 0
    )

    assert (
            summary.outside_top10_share
            == 0.0
    )

    assert summary.items == []


def test_mention_summary_defaults() -> None:
    summary = MentionSummary()

    assert summary.valid_count == 0
    assert summary.mentioned_count == 0
    assert summary.mention_rate == 0.0


def test_sentiment_summary_defaults() -> None:
    summary = SentimentSummary()

    assert (
            summary.classified_mention_count
            == 0
    )

    assert (
            summary.planned_mention_count
            == 0
    )

    assert summary.positive_count == 0
    assert summary.neutral_count == 0
    assert summary.negative_count == 0

    assert summary.non_negative_count == 0

    assert summary.non_negative_rate == 0.0

    assert (
            summary.classification_failed_count
            == 0
    )


def test_batch_analysis_summary_defaults() -> None:
    summary = BatchAnalysisSummary()

    assert summary.mention.valid_count == 0

    assert (
            summary.sentiment
            .classified_mention_count
            == 0
    )

    assert (
            summary.sources.total_occurrences
            == 0
    )


def test_target_mention_summary_defaults() -> None:
    summary = TargetMentionSummary(
        target_id="hongmao_yaojiu",
        target_name="鸿茅药酒",
    )

    assert summary.quick.valid_count == 0
    assert summary.expert.valid_count == 0
    assert summary.all_answers.valid_count == 0
    assert summary.question_level.valid_count == 0


def test_mention_batch_result_defaults() -> None:
    result = MentionBatchResult()

    assert result.details == {}
    assert result.summaries == {}


def test_target_sentiment_summary_defaults() -> None:
    summary = TargetSentimentSummary(
        target_id="hongmao_yaojiu",
        target_name="鸿茅药酒",
    )

    assert (
            summary.quick
            .classified_mention_count
            == 0
    )

    assert (
            summary.quick
            .non_negative_rate
            == 0.0
    )


def test_sentiment_batch_result_defaults() -> None:
    result = SentimentBatchResult()

    assert result.details == {}
    assert result.summaries == {}


def test_target_context_defaults() -> None:
    context = TargetContext()

    assert context.target_context == ""

    assert context.matched_aliases == []

    assert context.context_spans == []


def test_target_context_can_store_spans() -> None:
    context = TargetContext(
        target_context=(
            "鸿茅药酒属于药品。"
        ),
        matched_aliases=[
            "鸿茅药酒",
        ],
        context_spans=[
            {
                "alias": "鸿茅药酒",
                "start": 0,
                "end": 4,
                "sentence_index": 0,
            }
        ],
    )

    assert (
            context.matched_aliases
            == ["鸿茅药酒"]
    )

    assert (
            context.context_spans[0][
                "sentence_index"
            ]
            == 0
    )


def test_model_response_defaults() -> None:
    response = ModelResponse()

    assert response.payload == {}

    assert response.raw_content is None

    assert response.response_json_keys == []


def test_model_response_can_store_payload() -> None:
    response = ModelResponse(
        payload={
            "sentiment": "positive",
        },
        latency_seconds=0.5,
        total_tokens=100,
        raw_content=(
            '{"sentiment":"positive"}'
        ),
        response_json_keys=[
            "sentiment",
        ],
    )

    assert (
            response.payload["sentiment"]
            == "positive"
    )

    assert response.latency_seconds == 0.5

    assert response.total_tokens == 100


def test_sentiment_result_tracks_model_and_final_label() -> None:
    result = SentimentResult(
        target_id="hongmao_yaojiu",
        target_name="鸿茅药酒",
        status=SentimentStatus.SUCCESS,
        model_sentiment=(
            SentimentLabel.NEUTRAL
        ),
        final_sentiment=(
            SentimentLabel.NEGATIVE
        ),
        rule_hit=True,
        rule_override=True,
        override_applied=True,
        override_rule_codes=[
            "NEG_HONGMAO_FALSE_ADVERTISING"
        ],
    )

    assert (
            result.model_sentiment
            == SentimentLabel.NEUTRAL
    )

    assert (
            result.final_sentiment
            == SentimentLabel.NEGATIVE
    )

    assert result.rule_hit is True

    assert result.rule_override is True

    assert result.override_applied is True


def test_sentiment_result_rule_hit_without_override() -> None:
    result = SentimentResult(
        target_id="hongmao_yaojiu",
        status=SentimentStatus.SUCCESS,
        model_sentiment=(
            SentimentLabel.NEGATIVE
        ),
        final_sentiment=(
            SentimentLabel.NEGATIVE
        ),
        rule_hit=True,
        rule_override=False,
        override_applied=False,
        override_rule_codes=[
            "NEG_TAN_QINDONG_MENTION"
        ],
    )

    assert result.rule_hit is True

    assert result.rule_override is False

    assert result.override_applied is False


def test_sentiment_result_diagnostic_defaults() -> None:
    result = SentimentResult(
        target_id="hongmao_yaojiu",
        status=(
            SentimentStatus
            .NOT_APPLICABLE
        ),
    )

    assert result.evidence == []

    assert result.warnings == []

    assert result.override_rule_codes == []

    assert (
            result.suppressed_rule_candidates
            == []
    )

    assert (
            result.schema_coercion_fields
            == {}
    )


def test_geo_analysis_result_holds_all_analysis_layers() -> None:
    mention = MentionBatchResult()

    sentiment = SentimentBatchResult()

    sources = SourceTop10Summary(
        total_occurrences=10,
        top10_occurrences=8,
        top10_share=0.8,
        outside_top10_occurrences=2,
        outside_top10_share=0.2,
    )

    result = GeoAnalysisResult(
        mention=mention,
        sentiment=sentiment,
        sources=sources,
        source_mode=GeoMode.QUICK,
    )

    assert result.mention is mention

    assert result.sentiment is sentiment

    assert result.sources is sources

    assert (
            result.source_mode
            == GeoMode.QUICK
    )

    assert (
            result.sources.top10_share
            == 0.8
    )
