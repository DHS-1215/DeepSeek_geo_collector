import pytest

from app.analysis.mention_aggregator import (
    analyze_batch_mentions,
)
from app.analysis.models import (
    MentionTarget,
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
        status: TaskStatus = TaskStatus.SUCCESS,
        validation_status: (
                ValidationStatus
        ) = ValidationStatus.PASS,
) -> GeoRunResult:
    task = GeoTask(
        task_id=task_id,
        question_id=question_id,
        question=(
            f"{question_id} 测试问题"
        ),
        mode=mode,
    )

    return GeoRunResult(
        provider="deepseek",
        run_id=f"run_{task_id}",
        task=task,
        answer_text_raw=answer,
        answer_text_clean=answer,
        validation=ValidationResult(
            status=validation_status,
            is_complete=True,
        ),
        status=status,
    )


def test_quick_mention_rate() -> None:
    results = [
        _result(
            task_id="Q001_quick",
            question_id="Q001",
            mode=GeoMode.QUICK,
            answer="鸿茅药酒是药品。",
        ),
        _result(
            task_id="Q002_quick",
            question_id="Q002",
            mode=GeoMode.QUICK,
            answer="这是普通回答。",
        ),
    ]

    batch = analyze_batch_mentions(
        results=results,
        targets=[_target()],
    )

    summary = batch.summaries[
        "hongmao_yaojiu"
    ].quick

    assert summary.valid_count == 2

    assert summary.mentioned_count == 1

    assert summary.mention_rate == 0.5


def test_expert_mention_rate() -> None:
    results = [
        _result(
            task_id="Q001_expert",
            question_id="Q001",
            mode=GeoMode.EXPERT,
            answer="鸿茅药酒是药品。",
        ),
        _result(
            task_id="Q002_expert",
            question_id="Q002",
            mode=GeoMode.EXPERT,
            answer="鸿茅药酒需要合理使用。",
        ),
    ]

    batch = analyze_batch_mentions(
        results=results,
        targets=[_target()],
    )

    summary = batch.summaries[
        "hongmao_yaojiu"
    ].expert

    assert summary.valid_count == 2

    assert summary.mentioned_count == 2

    assert summary.mention_rate == 1.0


def test_all_answers_combines_modes() -> None:
    results = [
        _result(
            task_id="Q001_quick",
            question_id="Q001",
            mode=GeoMode.QUICK,
            answer="鸿茅药酒是药品。",
        ),
        _result(
            task_id="Q001_expert",
            question_id="Q001",
            mode=GeoMode.EXPERT,
            answer="普通回答。",
        ),
        _result(
            task_id="Q002_quick",
            question_id="Q002",
            mode=GeoMode.QUICK,
            answer="鸿茅药酒。",
        ),
        _result(
            task_id="Q002_expert",
            question_id="Q002",
            mode=GeoMode.EXPERT,
            answer="普通回答。",
        ),
    ]

    batch = analyze_batch_mentions(
        results=results,
        targets=[_target()],
    )

    summary = batch.summaries[
        "hongmao_yaojiu"
    ].all_answers

    assert summary.valid_count == 4

    assert summary.mentioned_count == 2

    assert summary.mention_rate == 0.5


def test_invalid_answer_not_in_denominator() -> None:
    results = [
        _result(
            task_id="Q001_quick",
            question_id="Q001",
            mode=GeoMode.QUICK,
            answer="鸿茅药酒。",
        ),
        _result(
            task_id="Q002_quick",
            question_id="Q002",
            mode=GeoMode.QUICK,
            answer="鸿茅药酒。",
            validation_status=(
                ValidationStatus.FAIL
            ),
        ),
    ]

    batch = analyze_batch_mentions(
        results=results,
        targets=[_target()],
    )

    summary = batch.summaries[
        "hongmao_yaojiu"
    ].quick

    assert summary.valid_count == 1

    assert summary.mentioned_count == 1

    assert summary.mention_rate == 1.0


def test_pass_with_warnings_is_in_denominator() -> None:
    results = [
        _result(
            task_id="Q001_quick",
            question_id="Q001",
            mode=GeoMode.QUICK,
            answer="普通回答。",
            validation_status=(
                ValidationStatus
                .PASS_WITH_WARNINGS
            ),
        ),
    ]

    batch = analyze_batch_mentions(
        results=results,
        targets=[_target()],
    )

    summary = batch.summaries[
        "hongmao_yaojiu"
    ].quick

    assert summary.valid_count == 1

    assert summary.mentioned_count == 0

    assert summary.mention_rate == 0.0


def test_question_level_combines_quick_and_expert() -> None:
    results = [
        _result(
            task_id="Q001_quick",
            question_id="Q001",
            mode=GeoMode.QUICK,
            answer="普通回答。",
        ),
        _result(
            task_id="Q001_expert",
            question_id="Q001",
            mode=GeoMode.EXPERT,
            answer="鸿茅药酒是药品。",
        ),
        _result(
            task_id="Q002_quick",
            question_id="Q002",
            mode=GeoMode.QUICK,
            answer="普通回答。",
        ),
        _result(
            task_id="Q002_expert",
            question_id="Q002",
            mode=GeoMode.EXPERT,
            answer="普通回答。",
        ),
    ]

    batch = analyze_batch_mentions(
        results=results,
        targets=[_target()],
    )

    summary = batch.summaries[
        "hongmao_yaojiu"
    ].question_level

    assert summary.valid_count == 2

    assert summary.mentioned_count == 1

    assert summary.mention_rate == 0.5


def test_question_without_valid_answers_is_excluded() -> None:
    results = [
        _result(
            task_id="Q001_quick",
            question_id="Q001",
            mode=GeoMode.QUICK,
            answer="鸿茅药酒。",
            validation_status=(
                ValidationStatus.FAIL
            ),
        ),
        _result(
            task_id="Q002_quick",
            question_id="Q002",
            mode=GeoMode.QUICK,
            answer="普通回答。",
        ),
    ]

    batch = analyze_batch_mentions(
        results=results,
        targets=[_target()],
    )

    summary = batch.summaries[
        "hongmao_yaojiu"
    ].question_level

    assert summary.valid_count == 1

    assert summary.mentioned_count == 0

    assert summary.mention_rate == 0.0


def test_batch_preserves_task_details() -> None:
    results = [
        _result(
            task_id="Q001_quick",
            question_id="Q001",
            mode=GeoMode.QUICK,
            answer="鸿茅药酒。",
        ),
    ]

    batch = analyze_batch_mentions(
        results=results,
        targets=[_target()],
    )

    assert (
            batch.details[
                "Q001_quick"
            ].mention_any
            is True
    )


def test_multiple_targets_are_aggregated_independently() -> None:
    second_target = MentionTarget(
        target_id="other_product",
        name="其他产品",
        aliases=[
            "其他产品",
        ],
    )

    results = [
        _result(
            task_id="Q001_quick",
            question_id="Q001",
            mode=GeoMode.QUICK,
            answer=(
                "鸿茅药酒和其他产品。"
            ),
        ),
    ]

    batch = analyze_batch_mentions(
        results=results,
        targets=[
            _target(),
            second_target,
        ],
    )

    assert (
            batch.summaries[
                "hongmao_yaojiu"
            ].quick.mention_rate
            == 1.0
    )

    assert (
            batch.summaries[
                "other_product"
            ].quick.mention_rate
            == 1.0
    )


def test_duplicate_target_id_rejected() -> None:
    with pytest.raises(
            ValueError,
            match="duplicate mention target_id",
    ):
        analyze_batch_mentions(
            results=[],
            targets=[
                _target(),
                _target(),
            ],
        )


def test_empty_batch_returns_zero_rates() -> None:
    batch = analyze_batch_mentions(
        results=[],
        targets=[_target()],
    )

    summary = batch.summaries[
        "hongmao_yaojiu"
    ]

    assert summary.quick.valid_count == 0
    assert summary.quick.mention_rate == 0.0

    assert summary.expert.valid_count == 0
    assert summary.expert.mention_rate == 0.0

    assert (
            summary.all_answers.valid_count
            == 0
    )

    assert (
            summary.question_level.valid_count
            == 0
    )
