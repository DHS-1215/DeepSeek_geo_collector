import asyncio
from pathlib import Path

from app.batch.checkpoint import (
    load_checkpoint,
    save_checkpoint,
)
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
        *,
        checkpoint_output_dir: Path | None = None,
) -> BatchResult:
    """
    串行执行一批 GEO 任务。

    checkpoint_output_dir 不为 None 时：
    - 自动恢复同 batch_id 已成功任务；
    - 已成功任务不会重复采集；
    - 每执行完一个任务立即更新 checkpoint；
    - FAILED 任务不会作为成功断点保存。
    """

    if not tasks:
        return BatchResult(
            batch_id="empty",
            status=BatchStatus.SUCCESS,
        )

    settings = load_settings()

    batch_id = tasks[0].batch_id

    task_ids = {
        task.task_id
        for task in tasks
    }

    results_by_task_id: dict[
        str,
        GeoRunResult,
    ] = {}

    if checkpoint_output_dir is not None:
        snapshot = load_checkpoint(
            output_dir=checkpoint_output_dir,
            batch_id=batch_id,
        )

        if snapshot is not None:
            if (
                    snapshot.checkpoint.total_count
                    != len(tasks)
            ):
                raise ValueError(
                    "Checkpoint task count mismatch: "
                    f"checkpoint="
                    f"{snapshot.checkpoint.total_count}, "
                    f"current={len(tasks)}"
                )

            for restored in snapshot.results:
                restored_task_id = (
                    restored.task.task_id
                )

                if restored_task_id not in task_ids:
                    raise ValueError(
                        "Checkpoint contains unknown "
                        "task_id: "
                        f"{restored_task_id}"
                    )

                if (
                        restored.status
                        != TaskStatus.SUCCESS
                ):
                    continue

                results_by_task_id[
                    restored_task_id
                ] = restored

            if results_by_task_id:
                print()
                print(
                    "[RESUME] 已恢复成功任务："
                    f"{len(results_by_task_id)}"
                    f" / {len(tasks)}"
                )

    for index, task in enumerate(
            tasks
    ):
        if task.task_id in results_by_task_id:
            print(
                "[RESUME] 跳过已完成任务："
                f"{task.task_id}"
            )
            continue

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

        results_by_task_id[
            task.task_id
        ] = run_result

        if checkpoint_output_dir is not None:
            save_checkpoint(
                output_dir=checkpoint_output_dir,
                batch_id=batch_id,
                total_count=len(tasks),
                results=list(
                    results_by_task_id.values()
                ),
                status="RUNNING",
            )

        has_next_task_to_execute = any(
            next_task.task_id
            not in results_by_task_id
            for next_task in tasks[
                index + 1:
            ]
        )

        if (
                has_next_task_to_execute
                and settings.task_interval_seconds > 0
        ):
            await asyncio.sleep(
                settings.task_interval_seconds
            )

    ordered_results = [
        results_by_task_id[
            task.task_id
        ]
        for task in tasks
        if task.task_id
        in results_by_task_id
    ]

    result = BatchResult(
        batch_id=batch_id,
        status=BatchStatus.RUNNING,
    )

    result.results.extend(
        ordered_results
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
        checkpoint_status = "INCOMPLETE"
    else:
        result.status = (
            BatchStatus.SUCCESS
        )
        checkpoint_status = "COMPLETED"

    if checkpoint_output_dir is not None:
        save_checkpoint(
            output_dir=checkpoint_output_dir,
            batch_id=batch_id,
            total_count=len(tasks),
            results=result.results,
            status=checkpoint_status,
        )

    return result
