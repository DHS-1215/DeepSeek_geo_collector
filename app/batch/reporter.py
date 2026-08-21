from dataclasses import dataclass

from app.batch.models import BatchResult


@dataclass(slots=True)
class BatchSummary:
    """
    批任务执行摘要。
    """

    batch_id: str

    status: str

    total_count: int

    success_count: int

    failed_count: int

    success_rate: float


def build_batch_summary(
        result: BatchResult,
) -> BatchSummary:
    """
    根据 BatchResult 生成执行摘要。
    """

    total = result.total_count

    success_rate = (
        result.success_count / total
        if total > 0
        else 0.0
    )

    return BatchSummary(
        batch_id=result.batch_id,

        status=result.status.value,

        total_count=total,

        success_count=(
            result.success_count
        ),

        failed_count=(
            result.failed_count
        ),

        success_rate=success_rate,
    )
