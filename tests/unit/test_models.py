from app.core.enums import (
    FailureType,
    GeoMode,
    TaskStatus,
    ValidationSeverity,
    ValidationStatus,
)
from app.core.models import (
    ArtifactInfo,
    FailureInfo,
    GeoRunResult,
    GeoSource,
    GeoTask,
    SourceCollection,
    SourceCollectionStatus,
    TimingInfo,
    ValidationIssue,
    ValidationResult,
)


def test_geo_task_creation() -> None:
    task = GeoTask(
        task_id="Q001_quick",
        question_id="Q001",
        question="测试问题",
        mode=GeoMode.QUICK,
    )
    assert task.task_id == "Q001_quick"
    assert task.question_id == "Q001"
    assert task.question == "测试问题"
    assert task.mode == GeoMode.QUICK


def test_geo_source_creation() -> None:
    source = GeoSource(
        occurrence_id="R1_S1",
        order=1,
        title="测试标题",
        resolved_url="https://example.com/page",
        domain="example.com",
    )

    assert source.occurrence_id == "R1_S1"
    assert source.order == 1
    assert source.title == "测试标题"
    assert source.domain == 'example.com'
    assert source.is_duplicate is False


def test_source_collection_has_independent_source_list() -> None:
    first = SourceCollection()
    second = SourceCollection()

    first.sources.append(
        GeoSource(
            occurrence_id="R1_S1",
            order=1,
        )
    )

    assert len(first.sources) == 1
    assert len(second.sources) == 0


def test_validation_result_creation() -> None:
    issue = ValidationIssue(
        code="SOURCE_COVERAGE_LOW",
        message="Source coverage is lower than expected.",
        severity=ValidationSeverity.WARNING,
    )

    validation = ValidationResult(
        ValidationStatus.PASS_WITH_WARNINGS,
        issues=[issue],
        is_complete=True,
    )

    assert validation.status == ValidationStatus.PASS_WITH_WARNINGS
    assert len(validation.issues) == 1
    assert validation.issues[0].code == "SOURCE_COVERAGE_LOW"


def test_failure_info_creation() -> None:
    failure = FailureInfo(
        type=FailureType.ANSWER_TIMEOUT,
        message="Answer generation timed out.",
        retryable=True,
    )

    assert failure.type == FailureType.ANSWER_TIMEOUT
    assert failure.retryable is True


def test_geo_run_result_defaults() -> None:
    task = GeoTask(
        task_id="Q001_quick",
        question_id="Q001",
        question="测试问题",
        mode=GeoMode.QUICK,
    )

    result = GeoRunResult(
        provider="deepseek",
        run_id="run_001",
        task=task,
    )

    assert result.provider == "deepseek"
    assert result.run_id == "run_001"

    assert result.batch_id is None
    assert result.answer_text_raw == ""
    assert result.answer_text_clean == ""

    assert result.status == TaskStatus.PENDING
    assert result.validation is None
    assert result.failure is None

    assert isinstance(result.sources, SourceCollection)
    assert isinstance(result.timing, TimingInfo)
    assert isinstance(result.artifacts, ArtifactInfo)


def test_geo_run_results_do_not_share_nested_objects() -> None:
    task1 = GeoTask(
        task_id="Q001_quick",
        question_id="Q001",
        question="问题1",
        mode=GeoMode.QUICK,
    )

    task2 = GeoTask(
        task_id="Q002_quick",
        question_id="Q002",
        question="问题2",
        mode=GeoMode.QUICK,
    )

    result1 = GeoRunResult(
        provider="deepseek",
        run_id="run_001",
        task=task1,
    )

    result2 = GeoRunResult(
        provider="deepseek",
        run_id="run_002",
        task=task2,
    )

    result1.sources.sources.append(
        GeoSource(
            occurrence_id="R1_S1",
            order=1,
        )
    )

    assert len(result1.sources.sources) == 1
    assert len(result2.sources.sources) == 0


def test_source_collection_default_status() -> None:
    collection = SourceCollection()

    assert collection.status == SourceCollectionStatus.NOT_APPLICABLE
