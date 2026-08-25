import pytest

from app.analysis.export_serialization import (
    build_analysis_document,
)
from app.analysis.models import (
    GeoAnalysisResult,
    MentionBatchResult,
    MentionResult,
    MentionSummary,
    SentimentBatchResult,
    SentimentLabel,
    SentimentResult,
    SentimentStatus,
    SentimentSummary,
    SourceRankItem,
    SourceTop10Summary,
    TargetMentionResult,
    TargetMentionSummary,
    TargetSentimentSummary,
)
from app.core.enums import GeoMode
from app.core.models import (
    GeoRunResult,
    GeoTask,
)


def _build_result() -> GeoRunResult:
    return GeoRunResult(
        provider="deepseek",
        run_id="run_001",
        batch_id="batch_001",
        task=GeoTask(
            task_id="batch_001_Q001_quick",
            question_id="Q001",
            question="鸿茅药酒是什么？",
            mode=GeoMode.QUICK,
        ),
    )


def _build_analysis() -> GeoAnalysisResult:
    task_id = (
        "batch_001_Q001_quick"
    )

    mention = MentionBatchResult(
        details={
            task_id: MentionResult(
                is_valid_answer=True,
                mention_any=True,
                mentioned_target_ids=[
                    "hongmao_yaojiu"
                ],
                target_results={
                    "hongmao_yaojiu": (
                        TargetMentionResult(
                            target_id=(
                                "hongmao_yaojiu"
                            ),
                            mention_count=1,
                            matched_terms=[
                                "鸿茅药酒"
                            ],
                        )
                    )
                },
            )
        },

        summaries={
            "hongmao_yaojiu": (
                TargetMentionSummary(
                    target_id=(
                        "hongmao_yaojiu"
                    ),
                    target_name="鸿茅药酒",
                    quick=MentionSummary(
                        valid_count=1,
                        mentioned_count=1,
                        mention_rate=1.0,
                    ),
                    all_answers=(
                        MentionSummary(
                            valid_count=1,
                            mentioned_count=1,
                            mention_rate=1.0,
                        )
                    ),
                    question_level=(
                        MentionSummary(
                            valid_count=1,
                            mentioned_count=1,
                            mention_rate=1.0,
                        )
                    ),
                )
            )
        },
    )

    sentiment = SentimentBatchResult(
        details={
            task_id: {
                "hongmao_yaojiu": (
                    SentimentResult(
                        target_id=(
                            "hongmao_yaojiu"
                        ),
                        target_name=(
                            "鸿茅药酒"
                        ),
                        status=(
                            SentimentStatus
                            .SUCCESS_WITH_WARNINGS
                        ),
                        mentioned=True,
                        matched_aliases=[
                            "鸿茅药酒"
                        ],
                        model_sentiment=(
                            SentimentLabel
                            .NEUTRAL
                        ),
                        final_sentiment=(
                            SentimentLabel
                            .NEGATIVE
                        ),
                        reason="模型原始原因",
                        evidence=[
                            "鸿茅药酒"
                        ],
                        confidence=0.8,
                        provider="ollama",
                        model_name=(
                            "qwen2.5:7b"
                        ),
                        prompt_version=(
                            "sentiment_v7"
                        ),
                        rule_version=(
                            "sentiment_rules_v5"
                        ),
                        rule_hit=True,
                        rule_override=True,
                        override_applied=True,
                        override_rule_codes=[
                            "NEG_TEST"
                        ],
                        override_reason=(
                            "业务规则覆盖原因"
                        ),
                    )
                )
            }
        },

        summaries={
            "hongmao_yaojiu": (
                TargetSentimentSummary(
                    target_id=(
                        "hongmao_yaojiu"
                    ),
                    target_name="鸿茅药酒",
                    quick=SentimentSummary(
                        planned_mention_count=1,
                        classified_mention_count=1,
                        negative_count=1,
                        non_negative_count=0,
                        negative_rate=1.0,
                        non_negative_rate=0.0,
                    ),
                    all_answers=(
                        SentimentSummary(
                            planned_mention_count=1,
                            classified_mention_count=1,
                            negative_count=1,
                            non_negative_count=0,
                            negative_rate=1.0,
                            non_negative_rate=0.0,
                        )
                    ),
                    question_level=(
                        SentimentSummary(
                            planned_mention_count=1,
                            classified_mention_count=1,
                            negative_count=1,
                            non_negative_count=0,
                            negative_rate=1.0,
                            non_negative_rate=0.0,
                        )
                    ),
                )
            )
        },
    )

    sources = SourceTop10Summary(
        total_occurrences=4,
        top10_occurrences=3,
        top10_share=0.75,
        outside_top10_occurrences=1,
        outside_top10_share=0.25,
        items=[
            SourceRankItem(
                source_key=(
                    "https://example.com/a"
                ),
                occurrence_count=3,
                question_count=1,
                average_order=2.0,
                first_seen_order=1,
                share=0.75,
                title="测试来源",
                site_name="example",
                canonical_url=(
                    "https://example.com/a"
                ),
            )
        ],
    )

    return GeoAnalysisResult(
        mention=mention,
        sentiment=sentiment,
        sources=sources,
        source_mode=GeoMode.QUICK,
    )


def test_build_analysis_document() -> None:
    document = (
        build_analysis_document(
            batch_id="batch_001",
            product_id=(
                "hongmao_yaojiu"
            ),
            product_name="鸿茅药酒",
            analysis=_build_analysis(),
            results=[
                _build_result()
            ],
        )
    )

    assert (
            document["schema_version"]
            == "geo_analysis_v1"
    )

    assert (
            document["platform_code"]
            == "deepseek"
    )

    assert (
            document["source_mode"]
            == "quick"
    )

    assert (
            document[
                "mention"
            ][
                "targets"
            ][
                "hongmao_yaojiu"
            ][
                "quick"
            ][
                "mention_rate"
            ]
            == 1.0
    )

    sentiment_detail = (
        document[
            "sentiment"
        ][
            "details"
        ][0]
    )

    assert (
            sentiment_detail["task_id"]
            == "batch_001_Q001_quick"
    )

    assert (
            sentiment_detail["question_id"]
            == "Q001"
    )

    assert (
            sentiment_detail["mode"]
            == "quick"
    )

    assert (
            sentiment_detail[
                "model_sentiment"
            ]
            == "neutral"
    )

    assert (
            sentiment_detail[
                "final_sentiment"
            ]
            == "negative"
    )

    assert (
            sentiment_detail[
                "effective_reason"
            ]
            == "业务规则覆盖原因"
    )

    assert (
            document[
                "sources"
            ][
                "top10_share"
            ]
            == 0.75
    )

    assert (
            document[
                "sources"
            ][
                "top10"
            ][0][
                "occurrence_count"
            ]
            == 3
    )


def test_analysis_document_rejects_unknown_task() -> None:
    analysis = _build_analysis()

    with pytest.raises(
            ValueError,
            match="unknown task_id",
    ):
        build_analysis_document(
            batch_id="batch_001",
            product_id=(
                "hongmao_yaojiu"
            ),
            product_name="鸿茅药酒",
            analysis=analysis,
            results=[],
        )


def test_analysis_document_rejects_empty_identity() -> None:
    with pytest.raises(
            ValueError,
            match="batch_id cannot be empty",
    ):
        build_analysis_document(
            batch_id="",
            product_id=(
                "hongmao_yaojiu"
            ),
            product_name="鸿茅药酒",
            analysis=_build_analysis(),
            results=[
                _build_result()
            ],
        )
