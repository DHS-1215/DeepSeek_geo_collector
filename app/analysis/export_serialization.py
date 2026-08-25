from typing import Any

from app.analysis.export_constants import (
    ANALYSIS_SCHEMA_VERSION,
    DEFAULT_ANALYSIS_PLATFORM_CODE,
)
from app.analysis.models import (
    GeoAnalysisResult,
    MentionResult,
    MentionSummary,
    SentimentResult,
    SentimentSummary,
    SourceRankItem,
    TargetMentionSummary,
    TargetSentimentSummary,
)
from app.core.models import GeoRunResult


def build_analysis_document(
        *,
        batch_id: str,
        product_id: str,
        product_name: str,
        analysis: GeoAnalysisResult,
        results: list[GeoRunResult],
        platform_code: str = (
                DEFAULT_ANALYSIS_PLATFORM_CODE
        ),
) -> dict[str, Any]:
    """
    将 GEO Analysis 结果序列化为
    geo_analysis_v1 Python dict。

    本函数只负责数据结构转换，
    不负责文件写入。
    """

    _validate_identity(
        batch_id=batch_id,
        product_id=product_id,
        product_name=product_name,
        platform_code=platform_code,
    )

    task_metadata = (
        _build_task_metadata(
            results
        )
    )

    return {
        "schema_version": (
            ANALYSIS_SCHEMA_VERSION
        ),

        "platform_code": (
            platform_code
        ),

        "batch_id": batch_id,

        "product": {
            "product_id": product_id,
            "product_name": product_name,
        },

        "metrics": _serialize_metrics(
            analysis
        ),

        "source_mode": (
            analysis.source_mode.value
        ),

        "mention": {
            "targets": {
                target_id: (
                    _serialize_target_mention(
                        summary
                    )
                )
                for target_id, summary
                in sorted(
                    analysis
                    .mention
                    .summaries
                    .items()
                )
            },

            "details": (
                _serialize_mention_details(
                    analysis=analysis,
                    task_metadata=(
                        task_metadata
                    ),
                )
            ),
        },

        "sentiment": {
            "targets": {
                target_id: (
                    _serialize_target_sentiment(
                        summary
                    )
                )
                for target_id, summary
                in sorted(
                    analysis
                    .sentiment
                    .summaries
                    .items()
                )
            },

            "details": (
                _serialize_sentiment_details(
                    analysis=analysis,
                    task_metadata=(
                        task_metadata
                    ),
                )
            ),
        },

        "sources": (
            _serialize_sources(
                analysis
            )
        ),
    }


def _build_task_metadata(
        results: list[GeoRunResult],
) -> dict[str, dict[str, str]]:
    metadata: dict[
        str,
        dict[str, str],
    ] = {}

    for result in results:
        task = result.task

        if task.task_id in metadata:
            raise ValueError(
                "duplicate task_id in "
                "analysis export results: "
                f"{task.task_id}"
            )

        metadata[
            task.task_id
        ] = {
            "question_id": (
                task.question_id
            ),
            "question": task.question,
            "mode": task.mode.value,
        }

    return metadata


def _serialize_mention_details(
        *,
        analysis: GeoAnalysisResult,
        task_metadata: dict[
            str,
            dict[str, str],
        ],
) -> list[dict[str, Any]]:
    rows: list[
        dict[str, Any]
    ] = []

    for task_id, mention in sorted(
            analysis
                    .mention
                    .details
                    .items()
    ):
        metadata = _require_task_metadata(
            task_id=task_id,
            task_metadata=task_metadata,
        )

        rows.append(
            {
                "task_id": task_id,

                "question_id": (
                    metadata[
                        "question_id"
                    ]
                ),

                "question": (
                    metadata[
                        "question"
                    ]
                ),

                "mode": (
                    metadata[
                        "mode"
                    ]
                ),

                **_serialize_mention_result(
                    mention
                ),
            }
        )

    return rows


def _serialize_mention_result(
        mention: MentionResult,
) -> dict[str, Any]:
    return {
        "is_valid_answer": (
            mention.is_valid_answer
        ),

        "mention_any": (
            mention.mention_any
        ),

        "mentioned_target_ids": list(
            mention.mentioned_target_ids
        ),

        "target_results": {
            target_id: {
                "target_id": (
                    target_result
                    .target_id
                ),

                "mention_count": (
                    target_result
                    .mention_count
                ),

                "matched_terms": list(
                    target_result
                    .matched_terms
                ),
            }
            for target_id, target_result
            in sorted(
                mention
                .target_results
                .items()
            )
        },
    }


def _serialize_target_mention(
        summary: TargetMentionSummary,
) -> dict[str, Any]:
    return {
        "target_id": (
            summary.target_id
        ),

        "target_name": (
            summary.target_name
        ),

        "quick": (
            _serialize_mention_summary(
                summary.quick
            )
        ),

        "expert": (
            _serialize_mention_summary(
                summary.expert
            )
        ),

        "all_answers": (
            _serialize_mention_summary(
                summary.all_answers
            )
        ),

        "question_level": (
            _serialize_mention_summary(
                summary.question_level
            )
        ),
    }


def _serialize_mention_summary(
        summary: MentionSummary,
) -> dict[str, Any]:
    return {
        "valid_count": (
            summary.valid_count
        ),

        "mentioned_count": (
            summary.mentioned_count
        ),

        "mention_rate": (
            summary.mention_rate
        ),
    }


def _serialize_sentiment_details(
        *,
        analysis: GeoAnalysisResult,
        task_metadata: dict[
            str,
            dict[str, str],
        ],
) -> list[dict[str, Any]]:
    rows: list[
        dict[str, Any]
    ] = []

    for task_id, target_results in sorted(
            analysis
                    .sentiment
                    .details
                    .items()
    ):
        metadata = _require_task_metadata(
            task_id=task_id,
            task_metadata=task_metadata,
        )

        for target_id, sentiment in sorted(
                target_results.items()
        ):
            rows.append(
                {
                    "task_id": task_id,

                    "question_id": (
                        metadata[
                            "question_id"
                        ]
                    ),

                    "question": (
                        metadata[
                            "question"
                        ]
                    ),

                    "mode": (
                        metadata[
                            "mode"
                        ]
                    ),

                    "target_id": (
                        target_id
                    ),

                    **_serialize_sentiment_result(
                        sentiment
                    ),
                }
            )

    return rows


def _serialize_sentiment_result(
        sentiment: SentimentResult,
) -> dict[str, Any]:
    effective_reason = (
        sentiment.override_reason
        if (
                sentiment.rule_override
                and sentiment.override_reason
        )
        else sentiment.reason
    )

    return {
        "status": (
            sentiment.status.value
        ),

        "target_name": (
            sentiment.target_name
        ),

        "mentioned": (
            sentiment.mentioned
        ),

        "matched_aliases": list(
            sentiment.matched_aliases
        ),

        "target_context": (
            sentiment.target_context
        ),

        "context_spans": list(
            sentiment.context_spans
        ),

        "model_sentiment": (
            sentiment
            .model_sentiment
            .value
            if (
                    sentiment.model_sentiment
                    is not None
            )
            else None
        ),

        "final_sentiment": (
            sentiment
            .final_sentiment
            .value
            if (
                    sentiment.final_sentiment
                    is not None
            )
            else None
        ),

        "reason": (
            sentiment.reason
        ),

        "effective_reason": (
            effective_reason
        ),

        "evidence": list(
            sentiment.evidence
        ),

        "confidence": (
            sentiment.confidence
        ),

        "provider": (
            sentiment.provider
        ),

        "model_name": (
            sentiment.model_name
        ),

        "prompt_version": (
            sentiment.prompt_version
        ),

        "rule_version": (
            sentiment.rule_version
        ),

        "rule_hit": (
            sentiment.rule_hit
        ),

        "rule_override": (
            sentiment.rule_override
        ),

        "override_applied": (
            sentiment.override_applied
        ),

        "override_rule_codes": list(
            sentiment.override_rule_codes
        ),

        "override_reason": (
            sentiment.override_reason
        ),

        "suppressed_rule_candidates": list(
            sentiment
            .suppressed_rule_candidates
        ),

        "warnings": list(
            sentiment.warnings
        ),

        "schema_coercion_applied": (
            sentiment
            .schema_coercion_applied
        ),

        "schema_coercion_fields": dict(
            sentiment
            .schema_coercion_fields
        ),

        "confidence_raw": (
            sentiment.confidence_raw
        ),

        "confidence_missing": (
            sentiment.confidence_missing
        ),

        "confidence_fallback_applied": (
            sentiment
            .confidence_fallback_applied
        ),

        "error_type": (
            sentiment.error_type
        ),

        "error_code": (
            sentiment.error_code
        ),

        "error_message": (
            sentiment.error_message
        ),

        "attempt_count": (
            sentiment.attempt_count
        ),

        "request_count": (
            sentiment.request_count
        ),

        "request_latencies": list(
            sentiment.request_latencies
        ),

        "retried": (
            sentiment.retried
        ),

        "latency_seconds": (
            sentiment.latency_seconds
        ),

        "prompt_tokens": (
            sentiment.prompt_tokens
        ),

        "completion_tokens": (
            sentiment
            .completion_tokens
        ),

        "total_tokens": (
            sentiment.total_tokens
        ),
    }


def _serialize_target_sentiment(
        summary: TargetSentimentSummary,
) -> dict[str, Any]:
    return {
        "target_id": (
            summary.target_id
        ),

        "target_name": (
            summary.target_name
        ),

        "quick": (
            _serialize_sentiment_summary(
                summary.quick
            )
        ),

        "expert": (
            _serialize_sentiment_summary(
                summary.expert
            )
        ),

        "all_answers": (
            _serialize_sentiment_summary(
                summary.all_answers
            )
        ),

        "question_level": (
            _serialize_sentiment_summary(
                summary.question_level
            )
        ),
    }


def _serialize_sentiment_summary(
        summary: SentimentSummary,
) -> dict[str, Any]:
    return {
        "planned_mention_count": (
            summary
            .planned_mention_count
        ),

        "classified_mention_count": (
            summary
            .classified_mention_count
        ),

        "positive_count": (
            summary.positive_count
        ),

        "neutral_count": (
            summary.neutral_count
        ),

        "negative_count": (
            summary.negative_count
        ),

        "non_negative_count": (
            summary.non_negative_count
        ),

        "positive_rate": (
            summary.positive_rate
        ),

        "neutral_rate": (
            summary.neutral_rate
        ),

        "negative_rate": (
            summary.negative_rate
        ),

        "non_negative_rate": (
            summary.non_negative_rate
        ),

        "classification_failed_count": (
            summary
            .classification_failed_count
        ),
    }


def _serialize_sources(
        analysis: GeoAnalysisResult,
) -> dict[str, Any]:
    summary = analysis.sources

    return {
        "total_occurrences": (
            summary.total_occurrences
        ),

        "top10_occurrences": (
            summary.top10_occurrences
        ),

        "top10_share": (
            summary.top10_share
        ),

        "outside_top10_occurrences": (
            summary
            .outside_top10_occurrences
        ),

        "outside_top10_share": (
            summary
            .outside_top10_share
        ),

        "top10": [
            _serialize_source_item(
                item
            )
            for item in summary.items
        ],
    }


def _serialize_source_item(
        item: SourceRankItem,
) -> dict[str, Any]:
    return {
        "source_key": (
            item.source_key
        ),

        "occurrence_count": (
            item.occurrence_count
        ),

        "question_count": (
            item.question_count
        ),

        "average_order": (
            item.average_order
        ),

        "first_seen_order": (
            item.first_seen_order
        ),

        "share": (
            item.share
        ),

        "title": item.title,

        "site_name": (
            item.site_name
        ),

        "canonical_url": (
            item.canonical_url
        ),
    }


def _require_task_metadata(
        *,
        task_id: str,
        task_metadata: dict[
            str,
            dict[str, str],
        ],
) -> dict[str, str]:
    metadata = task_metadata.get(
        task_id
    )

    if metadata is None:
        raise ValueError(
            "analysis references unknown "
            "task_id: "
            f"{task_id}"
        )

    return metadata


def _validate_identity(
        *,
        batch_id: str,
        product_id: str,
        product_name: str,
        platform_code: str,
) -> None:
    values = {
        "batch_id": batch_id,
        "product_id": product_id,
        "product_name": product_name,
        "platform_code": platform_code,
    }

    for field_name, value in values.items():
        if not value.strip():
            raise ValueError(
                f"{field_name} cannot be empty"
            )


def _serialize_metrics(
        analysis: GeoAnalysisResult,
) -> dict[str, Any]:
    return {
        "targets": {
            target_id: {
                "mention_rate": {
                    "quick": summary.quick.mention_rate,
                    "expert": summary.expert.mention_rate,
                    "all": summary.all_answers.mention_rate,
                    "question": summary.question_level.mention_rate,
                },
                "non_negative_rate": {
                    "quick": analysis.sentiment.summaries[target_id].quick.non_negative_rate,
                    "expert": analysis.sentiment.summaries[target_id].expert.non_negative_rate,
                    "all": analysis.sentiment.summaries[target_id].all_answers.non_negative_rate,
                    "question": analysis.sentiment.summaries[target_id].question_level.non_negative_rate,
                },
            }
            for target_id, summary in analysis.mention.summaries.items()
        },
        "source_top10_rate": analysis.sources.top10_share,
    }
