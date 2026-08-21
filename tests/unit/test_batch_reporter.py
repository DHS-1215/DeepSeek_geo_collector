from app.batch.models import (
    BatchResult,
    BatchStatus,
)
from app.batch.reporter import (
    build_batch_summary,
)


def test_build_batch_summary():
    result = BatchResult(
        batch_id="batch_001",
        status=BatchStatus.SUCCESS,
        total_count=10,
        success_count=8,
        failed_count=2,
    )

    summary = build_batch_summary(
        result
    )

    assert (
            summary.batch_id
            == "batch_001"
    )

    assert (
            summary.status
            == "success"
    )

    assert (
            summary.success_rate
            == 0.8
    )
