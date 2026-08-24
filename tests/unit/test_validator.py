from app.core.enums import (
    GeoMode,
    SourceCollectionStatus,
    TaskStatus,
    ValidationSeverity,
    ValidationStatus,
)
from app.core.models import (
    GeoRunResult,
    GeoTask,
    SourceCollection,
)
from app.validation.validator import (
    validate_run_result,
)


def _build_result(
        *,
        mode: GeoMode,
        task_status: TaskStatus = TaskStatus.SUCCESS,
        answer: str = "测试回答",
        source_status: SourceCollectionStatus = (
                SourceCollectionStatus.SUCCESS
        ),
) -> GeoRunResult:
    return GeoRunResult(
        provider="deepseek",
        run_id="run_test",
        task=GeoTask(
            task_id="task_001",
            question_id="Q001",
            question="测试问题",
            mode=mode,
        ),
        answer_text_raw=answer,
        answer_text_clean=answer,
        sources=SourceCollection(
            status=source_status,
        ),
        status=task_status,
    )


def test_validation_passes_successful_quick_result() -> None:
    result = _build_result(
        mode=GeoMode.QUICK,
    )

    validation = validate_run_result(
        result
    )

    assert (
            validation.status
            == ValidationStatus.PASS
    )

    assert validation.is_complete is True
    assert validation.issues == []


def test_validation_passes_expert_without_sources() -> None:
    result = _build_result(
        mode=GeoMode.EXPERT,
        source_status=(
            SourceCollectionStatus
            .NOT_APPLICABLE
        ),
    )

    validation = validate_run_result(
        result
    )

    assert (
            validation.status
            == ValidationStatus.PASS
    )

    assert validation.is_complete is True
    assert validation.issues == []


def test_validation_fails_empty_answer() -> None:
    result = _build_result(
        mode=GeoMode.QUICK,
        answer="",
    )

    validation = validate_run_result(
        result
    )

    assert (
            validation.status
            == ValidationStatus.FAIL
    )

    assert validation.is_complete is False

    assert (
            validation.issues[0].code
            == "ANSWER_EMPTY"
    )

    assert (
            validation.issues[0].severity
            == ValidationSeverity.ERROR
    )


def test_validation_fails_failed_task() -> None:
    result = _build_result(
        mode=GeoMode.QUICK,
        task_status=TaskStatus.FAILED,
        answer="",
    )

    validation = validate_run_result(
        result
    )

    assert (
            validation.status
            == ValidationStatus.FAIL
    )

    assert validation.is_complete is False

    assert (
            validation.issues[0].code
            == "TASK_FAILED"
    )


def test_validation_warns_for_partial_quick_sources() -> None:
    result = _build_result(
        mode=GeoMode.QUICK,
        source_status=(
            SourceCollectionStatus.PARTIAL
        ),
    )

    validation = validate_run_result(
        result
    )

    assert (
            validation.status
            == ValidationStatus.PASS_WITH_WARNINGS
    )

    assert validation.is_complete is True

    assert (
            validation.issues[0].code
            == "SOURCE_PARTIAL"
    )


def test_validation_warns_when_quick_sources_unavailable() -> None:
    result = _build_result(
        mode=GeoMode.QUICK,
        source_status=(
            SourceCollectionStatus
            .NOT_APPLICABLE
        ),
    )

    validation = validate_run_result(
        result
    )

    assert (
            validation.status
            == ValidationStatus.PASS_WITH_WARNINGS
    )

    assert validation.is_complete is True

    assert (
            validation.issues[0].code
            == "SOURCE_UNAVAILABLE"
    )
