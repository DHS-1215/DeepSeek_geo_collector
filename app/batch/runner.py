from app.batch.models import (
    BatchResult,
    BatchStatus,
    BatchTask,
)
from app.core.models import (
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

    batch_id = tasks[0].batch_id

    result = BatchResult(
        batch_id=batch_id,
        status=BatchStatus.RUNNING,
    )

    for task in tasks:
        geo_task = convert_to_geo_task(
            task
        )

        run_result = await run_deepseek_task(
            geo_task,
            batch_id=batch_id,
        )

        result.results.append(
            run_result
        )

    result.total_count = len(
        result.results
    )

    result.success_count = sum(
        1
        for item in result.results
        if item.status.value == "success"
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
