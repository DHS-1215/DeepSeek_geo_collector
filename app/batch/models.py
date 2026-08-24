from dataclasses import dataclass, field
from enum import Enum

from app.core.enums import GeoMode
from app.core.models import GeoRunResult


class BatchStatus(str, Enum):
    """
    批任务执行状态。
    """

    PENDING = "pending"

    RUNNING = "running"

    SUCCESS = "success"

    FAILED = "failed"


@dataclass(slots=True)
class BatchTask:
    """
    批处理中的单个任务。

    一个 BatchTask 最终会转换成一个 GeoTask，
    并交给 DeepSeek Runner 执行。
    """

    batch_id: str

    task_id: str

    question_id: str

    question: str

    mode: GeoMode


@dataclass(slots=True)
class BatchResult:
    """
    一次批处理执行结果。
    """

    batch_id: str

    status: BatchStatus = (
        BatchStatus.PENDING
    )

    results: list[GeoRunResult] = field(
        default_factory=list
    )

    total_count: int = 0

    success_count: int = 0

    failed_count: int = 0
