from dataclasses import dataclass
from enum import Enum
from pathlib import Path

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
    """

    status: PipelineStatus

    batch_result: BatchResult

    package_path: Path

    package_verified: bool
