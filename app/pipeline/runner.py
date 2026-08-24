from pathlib import Path

from app.batch.export import (
    export_batch_package,
)
from app.batch.loader import (
    load_batch_tasks,
)
from app.batch.runner import (
    run_batch,
)
from app.package.verifier import (
    verify_geo_package,
)
from app.pipeline.models import (
    PipelineResult,
    PipelineStatus,
)


async def run_collection_pipeline(
        *,
        csv_path: Path,
        batch_id: str,
        output_dir: Path,
        product_id: str,
        product_name: str,
) -> PipelineResult:
    """
    执行完整的 DeepSeek GEO 采集 Pipeline。
    """

    tasks = load_batch_tasks(
        csv_path=csv_path,
        batch_id=batch_id,
    )

    if not tasks:
        raise ValueError(
            "Batch CSV contains no tasks."
        )

    batch_result = await run_batch(
        tasks
    )

    package_path = export_batch_package(
        result=batch_result,
        output_dir=output_dir,
        product_id=product_id,
        product_name=product_name,
    )

    verify_geo_package(
        package_path
    )

    status = (
        PipelineStatus.PASS_WITH_WARNINGS
        if batch_result.failed_count > 0
        else PipelineStatus.PASS
    )

    return PipelineResult(
        status=status,
        batch_result=batch_result,
        package_path=package_path,
        package_verified=True,
    )
