import asyncio

from app.batch.models import (
    BatchResult,
    BatchStatus,
    BatchTask,
)
from app.core.config import load_settings
from app.core.enums import TaskStatus
from app.core.models import (
    GeoRunResult,
    GeoTask,
)
from app.deepseek.runner import (
    run_deepseek_task,
)


def convert_to_geo_task(
        task: BatchTask,
) -> GeoTask:
    """
    将 BatchTask 转换为 GEO 执行任务。
    """

    return GeoTask(
        task_id=task.task_id,
        question_id=task.question_id,
        question=task.question,
        mode=task.mode,
    )


async def run_task_with_retry(
        task: GeoTask,
        batch_id: str,
        max_retries: int,
        retry_interval_seconds: int,
) -> GeoRunResult:
    """
    执行单个任务，并对可重试失败进行自动重试。

    max_retries 表示首次执行失败后，
    最多额外重试多少次。
    """

    retry_count = 0

    while True:
        run_result = await run_deepseek_task(
            task,
            batch_id=batch_id,
        )

        if (
                run_result.status
                == TaskStatus.SUCCESS
        ):
            return run_result

        failure = run_result.failure

        if (
                failure is None
                or not failure.retryable
        ):
            return run_result

        if retry_count >= max_retries:
            return run_result

        retry_count += 1

        if retry_interval_seconds > 0:
            await asyncio.sleep(
                retry_interval_seconds
            )


async def run_batch(
        tasks: list[BatchTask],
) -> BatchResult:
    """
    串行执行一批 GEO 任务。
    """

    if not tasks:
        return BatchResult(
            batch_id="empty",
            status=BatchStatus.SUCCESS,
        )

    settings = load_settings()

    batch_id = tasks[0].batch_id

    result = BatchResult(
        batch_id=batch_id,
        status=BatchStatus.RUNNING,
    )

    for index, task in enumerate(
            tasks
    ):
        geo_task = convert_to_geo_task(
            task
        )

        run_result = await run_task_with_retry(
            geo_task,
            batch_id=batch_id,
            max_retries=(
                settings.network_retry_times
            ),
            retry_interval_seconds=(
                settings
                .network_retry_interval_seconds
            ),
        )

        result.results.append(
            run_result
        )

        has_next_task = (
                index
                <
                len(tasks) - 1
        )

        if (
                has_next_task
                and settings.task_interval_seconds > 0
        ):
            await asyncio.sleep(
                settings.task_interval_seconds
            )

    result.total_count = len(
        result.results
    )

    result.success_count = sum(
        1
        for item in result.results
        if item.status == TaskStatus.SUCCESS
    )

    result.failed_count = (
            result.total_count
            -
            result.success_count
    )

    if result.failed_count:
        result.status = (
            BatchStatus.FAILED
        )
    else:
        result.status = (
            BatchStatus.SUCCESS
        )

    return result
