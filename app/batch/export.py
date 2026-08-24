from pathlib import Path

from app.batch.models import BatchResult
from app.package.exporter import (
    export_geo_package,
)


def export_batch_package(
        result: BatchResult,
        output_dir: Path,
        product_id: str,
        product_name: str,
) -> Path:
    """
    将批任务结果导出为 GEO Package。
    """

    return export_geo_package(
        batch_id=result.batch_id,
        results=result.results,
        output_dir=output_dir,
        product_id=product_id,
        product_name=product_name,
    )