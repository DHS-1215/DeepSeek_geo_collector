from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from app.analysis.models import (
    GeoAnalysisResult,
)
from app.batch.models import BatchResult


class PipelineStatus(str, Enum):
    """
    Pipeline 最终状态。
    """

    PASS = "PASS"

    PASS_WITH_WARNINGS = (
        "PASS_WITH_WARNINGS"
    )


@dataclass(slots=True)
class PipelineResult:
    """
    一次完整 GEO Pipeline 的执行结果。

    batch_result:
        原始 DeepSeek Batch 采集结果。

    analysis_result:
        基于采集结果生成的统一 GEO Analysis。

    package_path:
        geo_package_v1 导出路径。

    package_verified:
        Package 是否通过完整性校验。
    """

    status: PipelineStatus

    batch_result: BatchResult

    analysis_result: GeoAnalysisResult

    package_path: Path

    package_verified: bool