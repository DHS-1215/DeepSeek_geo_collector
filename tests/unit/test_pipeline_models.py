from pathlib import Path

from app.batch.models import (
    BatchResult,
    BatchStatus,
)
from app.pipeline.models import (
    PipelineResult,
    PipelineStatus,
)


def test_pipeline_status_values() -> None:
    assert (
            PipelineStatus.PASS.value
            == "PASS"
    )

    assert (
            PipelineStatus.PASS_WITH_WARNINGS.value
            == "PASS_WITH_WARNINGS"
    )


def test_pipeline_result_holds_completed_pipeline_data() -> None:
    batch_result = BatchResult(
        batch_id="batch_001",
        status=BatchStatus.SUCCESS,
        total_count=2,
        success_count=2,
        failed_count=0,
    )

    package_path = Path(
        "output/package/test.zip"
    )

    result = PipelineResult(
        status=PipelineStatus.PASS,
        batch_result=batch_result,
        package_path=package_path,
        package_verified=True,
    )

    assert (
            result.status
            == PipelineStatus.PASS
    )

    assert (
            result.batch_result
            is batch_result
    )

    assert (
            result.package_path
            == package_path
    )

    assert (
            result.package_verified
            is True
    )
