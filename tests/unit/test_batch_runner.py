from unittest.mock import AsyncMock
import asyncio
import pytest

from app.batch.models import (
    BatchStatus,
    BatchTask,
)
from app.batch.runner import (
    run_batch,
)
from app.core.enums import (
    GeoMode,
    TaskStatus,
)
from app.core.models import (
    GeoRunResult,
    GeoTask,
)

def test_run_batch_success(
        monkeypatch,
):
    async def fake_runner(
            task: GeoTask,
            batch_id: str,
    ):
        return GeoRunResult(
            provider="deepseek",
            run_id="run_test",
            task=task,
            batch_id=batch_id,
            status=TaskStatus.SUCCESS,
        )

    monkeypatch.setattr(
        "app.batch.runner.run_deepseek_task",
        fake_runner,
    )

    tasks = [
        BatchTask(
            batch_id="batch_001",
            task_id="task_001",
            question_id="Q001",
            question="测试问题",
            mode=GeoMode.QUICK,
        )
    ]

    result = asyncio.run(
        run_batch(tasks)
    )

    assert result.status == (
        BatchStatus.SUCCESS
    )

    assert result.total_count == 1

    assert result.success_count == 1

    assert result.failed_count == 0
