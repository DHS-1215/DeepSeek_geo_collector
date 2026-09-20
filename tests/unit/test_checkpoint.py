from pathlib import Path

from app.batch.checkpoint import (
    load_checkpoint,
    save_checkpoint,
)
from app.core.enums import (
    GeoMode,
    SourceCollectionStatus,
    TaskStatus,
    ValidationSeverity,
    ValidationStatus,
)
from app.core.models import (
    ArtifactInfo,
    GeoRunResult,
    GeoSource,
    GeoTask,
    SourceCollection,
    TimingInfo,
    ValidationIssue,
    ValidationResult,
)


def test_checkpoint_roundtrip(
        tmp_path: Path,
) -> None:
    batch_id = "batch_resume_test"

    success_result = GeoRunResult(
        provider="deepseek",
        run_id="run_success_001",
        batch_id=batch_id,
        task=GeoTask(
            task_id="Q001_quick",
            question_id="Q001",
            question="测试问题",
            mode=GeoMode.QUICK,
        ),
        answer_text_raw="原始回答",
        answer_text_clean="清洗后的回答",
        sources=SourceCollection(
            status=(
                SourceCollectionStatus.SUCCESS
            ),
            declared_count=2,
            captured_count=2,
            unique_count=2,
            coverage_ratio=1.0,
            sources=[
                GeoSource(
                    occurrence_id="source_001",
                    order=1,
                    title="测试来源",
                    clean_title="测试来源",
                    site_name="测试网站",
                    resolved_url=(
                        "https://example.com/a"
                    ),
                    domain="example.com",
                    snippet="测试摘要",
                ),
            ],
        ),
        timing=TimingInfo(
            started_at=(
                "2026-09-20T09:00:00"
            ),
            finished_at=(
                "2026-09-20T09:00:10"
            ),
            elapsed_seconds=10.0,
        ),
        artifacts=ArtifactInfo(
            screenshot_path=(
                "output/test.png"
            ),
        ),
        validation=ValidationResult(
            status=ValidationStatus.PASS,
            issues=[
                ValidationIssue(
                    code="TEST_WARNING",
                    message="测试提示",
                    severity=(
                        ValidationSeverity.WARNING
                    ),
                ),
            ],
            is_complete=True,
        ),
        status=TaskStatus.SUCCESS,
    )

    failed_result = GeoRunResult(
        provider="deepseek",
        run_id="run_failed_001",
        batch_id=batch_id,
        task=GeoTask(
            task_id="Q002_quick",
            question_id="Q002",
            question="失败问题",
            mode=GeoMode.QUICK,
        ),
        status=TaskStatus.FAILED,
    )

    checkpoint = save_checkpoint(
        output_dir=tmp_path,
        batch_id=batch_id,
        total_count=2,
        results=[
            success_result,
            failed_result,
        ],
    )

    assert checkpoint.total_count == 2
    assert checkpoint.successful_count == 1
    assert (
        checkpoint.successful_task_ids
        == ["Q001_quick"]
    )

    snapshot = load_checkpoint(
        output_dir=tmp_path,
        batch_id=batch_id,
    )

    assert snapshot is not None

    assert (
        snapshot.checkpoint.batch_id
        == batch_id
    )

    assert (
        snapshot.checkpoint.successful_count
        == 1
    )

    assert len(snapshot.results) == 1

    restored = snapshot.results[0]

    assert restored == success_result

    assert (
        restored.task.mode
        == GeoMode.QUICK
    )

    assert (
        restored.sources.status
        == SourceCollectionStatus.SUCCESS
    )

    assert (
        restored.validation is not None
    )

    assert (
        restored.validation.status
        == ValidationStatus.PASS
    )
