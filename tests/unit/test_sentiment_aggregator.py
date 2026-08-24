import asyncio

import pytest

from app.analysis.mention_aggregator import (
    analyze_batch_mentions,
)
from app.analysis.models import (
    MentionTarget,
    SentimentLabel,
)
from app.analysis.sentiment_aggregator import (
    analyze_batch_sentiment,
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


class MappingClassifier:
    name = "mapping-classifier"

    def __init__(
            self,
            labels: dict[str, str],
    ) -> None:
        self.labels = labels

    async def classify(
            self,
            *,
            answer_text: str,
            target: MentionTarget,
    ) -> str:
        if answer_text not in self.labels:
            raise RuntimeError(
                "missing test label"
            )

        return self.labels[
            answer_text
        ]


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
        mode: GeoMode,
        answer: str,
        validation_status: (
                ValidationStatus
        ) = ValidationStatus.PASS,
) -> GeoRunResult:
    return GeoRunResult(
        provider="deepseek",

        run_id=f"run_{task_id}",

        task=GeoTask(
            task_id=task_id,
            question_id=question_id,
            question=f"{question_id} 问题",
            mode=mode,
        ),

        answer_text_raw=answer,

        answer_text_clean=answer,

        validation=ValidationResult(
            status=validation_status,
            is_complete=True,
        ),

        status=TaskStatus.SUCCESS,
    )


def _analyze(
        results: list[GeoRunResult],
        labels: dict[str, str],
):
    targets = [
        _target()
    ]

    mention_batch = (
        analyze_batch_mentions(
            results=results,
            targets=targets,
        )
    )

    return asyncio.run(
        analyze_batch_sentiment(
            results=results,
            mention_batch=mention_batch,
            targets=targets,
            classifier=(
                MappingClassifier(
                    labels
                )
            ),
        )
    )


def test_non_negative_rate() -> None:
    results = [
        _result(
            task_id="Q001_quick",
            question_id="Q001",
            mode=GeoMode.QUICK,
            answer="鸿茅药酒正向。",
        ),

        _result(
            task_id="Q002_quick",
            question_id="Q002",
            mode=GeoMode.QUICK,
            answer="鸿茅药酒中性。",
        ),

        _result(
            task_id="Q003_quick",
            question_id="Q003",
            mode=GeoMode.QUICK,
            answer="鸿茅药酒负向。",
        ),
    ]

    batch = _analyze(
        results,
        {
            "鸿茅药酒正向。":
                "positive",

            "鸿茅药酒中性。":
                "neutral",

            "鸿茅药酒负向。":
                "negative",
        },
    )

    summary = batch.summaries[
        "hongmao_yaojiu"
    ].quick

    assert (
            summary.planned_mention_count
            == 3
    )

    assert (
            summary.classified_mention_count
            == 3
    )

    assert summary.positive_count == 1
    assert summary.neutral_count == 1
    assert summary.negative_count == 1

    assert summary.non_negative_count == 2

    assert (
            summary.non_negative_rate
            == pytest.approx(
        2 / 3
    )
    )


def test_unmentioned_answer_not_planned() -> None:
    results = [
        _result(
            task_id="Q001_quick",
            question_id="Q001",
            mode=GeoMode.QUICK,
            answer="普通回答。",
        ),
    ]

    batch = _analyze(
        results,
        {},
    )

    summary = batch.summaries[
        "hongmao_yaojiu"
    ].quick

    assert (
            summary.planned_mention_count
            == 0
    )

    assert (
            summary.classified_mention_count
            == 0
    )

    assert (
            summary.non_negative_rate
            == 0.0
    )


def test_classification_failure_not_in_rate_denominator() -> None:
    results = [
        _result(
            task_id="Q001_quick",
            question_id="Q001",
            mode=GeoMode.QUICK,
            answer="鸿茅药酒成功。",
        ),

        _result(
            task_id="Q002_quick",
            question_id="Q002",
            mode=GeoMode.QUICK,
            answer="鸿茅药酒失败。",
        ),
    ]

    batch = _analyze(
        results,
        {
            "鸿茅药酒成功。":
                "positive",
        },
    )

    summary = batch.summaries[
        "hongmao_yaojiu"
    ].quick

    assert (
            summary.planned_mention_count
            == 2
    )

    assert (
            summary.classified_mention_count
            == 1
    )

    assert (
            summary.classification_failed_count
            == 1
    )

    assert (
            summary.non_negative_rate
            == 1.0
    )


def test_quick_and_expert_are_separate() -> None:
    results = [
        _result(
            task_id="Q001_quick",
            question_id="Q001",
            mode=GeoMode.QUICK,
            answer="鸿茅药酒正向。",
        ),

        _result(
            task_id="Q001_expert",
            question_id="Q001",
            mode=GeoMode.EXPERT,
            answer="鸿茅药酒负向。",
        ),
    ]

    batch = _analyze(
        results,
        {
            "鸿茅药酒正向。":
                "positive",

            "鸿茅药酒负向。":
                "negative",
        },
    )

    target = batch.summaries[
        "hongmao_yaojiu"
    ]

    assert (
            target.quick.positive_count
            == 1
    )

    assert (
            target.expert.negative_count
            == 1
    )

    assert (
            target.all_answers
            .classified_mention_count
            == 2
    )


def test_question_level_negative_has_priority() -> None:
    results = [
        _result(
            task_id="Q001_quick",
            question_id="Q001",
            mode=GeoMode.QUICK,
            answer="鸿茅药酒正向。",
        ),

        _result(
            task_id="Q001_expert",
            question_id="Q001",
            mode=GeoMode.EXPERT,
            answer="鸿茅药酒负向。",
        ),
    ]

    batch = _analyze(
        results,
        {
            "鸿茅药酒正向。":
                "positive",

            "鸿茅药酒负向。":
                "negative",
        },
    )

    summary = batch.summaries[
        "hongmao_yaojiu"
    ].question_level

    assert (
            summary.planned_mention_count
            == 1
    )

    assert (
            summary.classified_mention_count
            == 1
    )

    assert summary.negative_count == 1

    assert (
            summary.non_negative_rate
            == 0.0
    )


def test_question_level_positive_over_neutral() -> None:
    results = [
        _result(
            task_id="Q001_quick",
            question_id="Q001",
            mode=GeoMode.QUICK,
            answer="鸿茅药酒中性。",
        ),

        _result(
            task_id="Q001_expert",
            question_id="Q001",
            mode=GeoMode.EXPERT,
            answer="鸿茅药酒正向。",
        ),
    ]

    batch = _analyze(
        results,
        {
            "鸿茅药酒中性。":
                "neutral",

            "鸿茅药酒正向。":
                "positive",
        },
    )

    summary = batch.summaries[
        "hongmao_yaojiu"
    ].question_level

    assert summary.positive_count == 1

    assert summary.neutral_count == 0

    assert (
            summary.non_negative_rate
            == 1.0
    )


def test_question_level_all_failed() -> None:
    results = [
        _result(
            task_id="Q001_quick",
            question_id="Q001",
            mode=GeoMode.QUICK,
            answer="鸿茅药酒失败。",
        ),
    ]

    batch = _analyze(
        results,
        {},
    )

    summary = batch.summaries[
        "hongmao_yaojiu"
    ].question_level

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


def test_sentiment_details_are_preserved() -> None:
    results = [
        _result(
            task_id="Q001_quick",
            question_id="Q001",
            mode=GeoMode.QUICK,
            answer="鸿茅药酒正向。",
        ),
    ]

    batch = _analyze(
        results,
        {
            "鸿茅药酒正向。":
                "positive",
        },
    )

    result = (
        batch.details[
            "Q001_quick"
        ][
            "hongmao_yaojiu"
        ]
    )

    assert (
            result.final_sentiment
            == SentimentLabel.POSITIVE
    )


def test_missing_mention_detail_rejected() -> None:
    results = [
        _result(
            task_id="Q001_quick",
            question_id="Q001",
            mode=GeoMode.QUICK,
            answer="鸿茅药酒。",
        ),
    ]

    mention_batch = (
        analyze_batch_mentions(
            results=[],
            targets=[_target()],
        )
    )

    with pytest.raises(
            ValueError,
            match="missing mention result",
    ):
        asyncio.run(
            analyze_batch_sentiment(
                results=results,
                mention_batch=(
                    mention_batch
                ),
                targets=[_target()],
                classifier=(
                    MappingClassifier(
                        {}
                    )
                ),
            )
        )


def test_empty_batch_returns_zero_rates() -> None:
    batch = _analyze(
        [],
        {},
    )

    summary = batch.summaries[
        "hongmao_yaojiu"
    ]

    assert (
            summary.quick
            .classified_mention_count
            == 0
    )

    assert (
            summary.expert
            .non_negative_rate
            == 0.0
    )

    assert (
            summary.all_answers
            .non_negative_rate
            == 0.0
    )

    assert (
            summary.question_level
            .non_negative_rate
            == 0.0
    )
