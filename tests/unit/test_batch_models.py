from app.batch.models import (
    BatchResult,
    BatchStatus,
    BatchTask,
)
from app.core.enums import GeoMode


def test_batch_task_create():
    task = BatchTask(
        batch_id="batch_001",
        task_id="task_001",
        question_id="Q001",
        question="测试问题",
        mode=GeoMode.QUICK,
    )

    assert task.batch_id == "batch_001"

    assert task.mode == GeoMode.QUICK


def test_batch_result_default():
    result = BatchResult(
        batch_id="batch_001",
    )

    assert result.status == (
        BatchStatus.PENDING
    )

    assert result.results == []

    assert result.total_count == 0
