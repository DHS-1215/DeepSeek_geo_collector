import asyncio

from app.batch.models import (
    BatchStatus,
    BatchTask,
)
from app.batch.runner import (
    run_batch,
    run_task_with_retry,
)
from app.core.enums import (
    GeoMode,
    TaskStatus, FailureType,
)
from app.core.models import (
    GeoRunResult,
    GeoTask,
    FailureInfo,
)
from types import SimpleNamespace
from unittest.mock import AsyncMock


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


def test_run_batch_continues_after_failed_result(
        monkeypatch,
):
    executed_task_ids = []

    async def fake_runner(
            task: GeoTask,
            batch_id: str,
    ):
        executed_task_ids.append(
            task.task_id
        )

        status = (
            TaskStatus.FAILED
            if task.task_id == "task_002"
            else TaskStatus.SUCCESS
        )

        return GeoRunResult(
            provider="deepseek",
            run_id=f"run_{task.task_id}",
            task=task,
            batch_id=batch_id,
            status=status,
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
            question="测试问题1",
            mode=GeoMode.QUICK,
        ),
        BatchTask(
            batch_id="batch_001",
            task_id="task_002",
            question_id="Q002",
            question="测试问题2",
            mode=GeoMode.QUICK,
        ),
        BatchTask(
            batch_id="batch_001",
            task_id="task_003",
            question_id="Q003",
            question="测试问题3",
            mode=GeoMode.QUICK,
        ),
    ]

    result = asyncio.run(
        run_batch(tasks)
    )

    assert executed_task_ids == [
        "task_001",
        "task_002",
        "task_003",
    ]

    assert result.total_count == 3

    assert result.success_count == 2

    assert result.failed_count == 1

    assert result.status == (
        BatchStatus.FAILED
    )

    assert len(result.results) == 3


def test_run_task_with_retry_succeeds_after_retry(
        monkeypatch,
):
    import app.batch.runner as runner

    call_count = 0

    async def fake_runner(
            task: GeoTask,
            batch_id: str,
    ):
        nonlocal call_count

        call_count += 1

        if call_count == 1:
            return GeoRunResult(
                provider="deepseek",
                run_id="run_failed",
                task=task,
                batch_id=batch_id,
                failure=FailureInfo(
                    type=FailureType.ANSWER_TIMEOUT,
                    message="timeout",
                    retryable=True,
                ),
                status=TaskStatus.FAILED,
            )

        return GeoRunResult(
            provider="deepseek",
            run_id="run_success",
            task=task,
            batch_id=batch_id,
            status=TaskStatus.SUCCESS,
        )

    monkeypatch.setattr(
        runner,
        "run_deepseek_task",
        fake_runner,
    )

    task = GeoTask(
        task_id="task_retry",
        question_id="Q001",
        question="重试测试",
        mode=GeoMode.QUICK,
    )

    result = asyncio.run(
        run_task_with_retry(
            task,
            batch_id="batch_001",
            max_retries=2,
            retry_interval_seconds=0,
        )
    )

    assert call_count == 2

    assert (
            result.status
            == TaskStatus.SUCCESS
    )


def test_run_task_with_retry_stops_after_max_retries(
        monkeypatch,
):
    import app.batch.runner as runner

    call_count = 0

    async def fake_runner(
            task: GeoTask,
            batch_id: str,
    ):
        nonlocal call_count

        call_count += 1

        return GeoRunResult(
            provider="deepseek",
            run_id=f"run_{call_count}",
            task=task,
            batch_id=batch_id,
            failure=FailureInfo(
                type=FailureType.ANSWER_TIMEOUT,
                message="timeout",
                retryable=True,
            ),
            status=TaskStatus.FAILED,
        )

    monkeypatch.setattr(
        runner,
        "run_deepseek_task",
        fake_runner,
    )

    task = GeoTask(
        task_id="task_retry",
        question_id="Q001",
        question="重试上限测试",
        mode=GeoMode.QUICK,
    )

    result = asyncio.run(
        run_task_with_retry(
            task,
            batch_id="batch_001",
            max_retries=2,
            retry_interval_seconds=0,
        )
    )

    assert call_count == 3

    assert (
            result.status
            == TaskStatus.FAILED
    )

    assert result.failure is not None

    assert (
            result.failure.type
            == FailureType.ANSWER_TIMEOUT
    )


def test_run_task_with_retry_does_not_retry_non_retryable_failure(
        monkeypatch,
):
    import app.batch.runner as runner

    call_count = 0

    async def fake_runner(
            task: GeoTask,
            batch_id: str,
    ):
        nonlocal call_count

        call_count += 1

        return GeoRunResult(
            provider="deepseek",
            run_id="run_failed",
            task=task,
            batch_id=batch_id,
            failure=FailureInfo(
                type=FailureType.UI_CHANGED,
                message="selector changed",
                retryable=False,
            ),
            status=TaskStatus.FAILED,
        )

    monkeypatch.setattr(
        runner,
        "run_deepseek_task",
        fake_runner,
    )

    task = GeoTask(
        task_id="task_no_retry",
        question_id="Q001",
        question="不可重试测试",
        mode=GeoMode.QUICK,
    )

    result = asyncio.run(
        run_task_with_retry(
            task,
            batch_id="batch_001",
            max_retries=2,
            retry_interval_seconds=0,
        )
    )

    assert call_count == 1

    assert (
            result.status
            == TaskStatus.FAILED
    )

    assert result.failure is not None

    assert (
            result.failure.type
            == FailureType.UI_CHANGED
    )


def test_run_batch_waits_only_between_tasks(
        monkeypatch,
):
    import app.batch.runner as runner

    settings = SimpleNamespace(
        network_retry_times=2,
        network_retry_interval_seconds=3,
        task_interval_seconds=5,
    )

    monkeypatch.setattr(
        runner,
        "load_settings",
        lambda: settings,
    )

    async def fake_run_task_with_retry(
            task: GeoTask,
            batch_id: str,
            max_retries: int,
            retry_interval_seconds: int,
    ):
        return GeoRunResult(
            provider="deepseek",
            run_id=f"run_{task.task_id}",
            task=task,
            batch_id=batch_id,
            status=TaskStatus.SUCCESS,
        )

    monkeypatch.setattr(
        runner,
        "run_task_with_retry",
        fake_run_task_with_retry,
    )

    sleep_mock = AsyncMock()

    monkeypatch.setattr(
        runner.asyncio,
        "sleep",
        sleep_mock,
    )

    tasks = [
        BatchTask(
            batch_id="batch_001",
            task_id="task_001",
            question_id="Q001",
            question="测试问题1",
            mode=GeoMode.QUICK,
        ),
        BatchTask(
            batch_id="batch_001",
            task_id="task_002",
            question_id="Q002",
            question="测试问题2",
            mode=GeoMode.QUICK,
        ),
        BatchTask(
            batch_id="batch_001",
            task_id="task_003",
            question_id="Q003",
            question="测试问题3",
            mode=GeoMode.QUICK,
        ),
    ]

    result = asyncio.run(
        run_batch(tasks)
    )

    assert (
            result.status
            == BatchStatus.SUCCESS
    )

    assert result.total_count == 3

    assert sleep_mock.await_count == 2

    sleep_mock.assert_awaited_with(
        5
    )
