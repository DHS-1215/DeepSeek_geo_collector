from dataclasses import dataclass, field
from app.core.enums import (
    FailureType,
    GeoMode,
    TaskStatus,
    ValidationSeverity,
    ValidationStatus,
    SourceCollectionStatus,
)


@dataclass(slots=True)
class GeoTask:
    """单个GEO采集任务"""
    task_id: str
    question_id: str
    question: str
    mode: GeoMode


@dataclass(slots=True)
class GeoSource:
    """单条 GEO 引用信源。"""
    occurrence_id: str
    order: int

    title: str | None = None
    clean_title: str | None = None
    site_name: str | None = None

    raw_href: str | None = None
    resolved_url: str | None = None
    domain: str | None = None

    source_round: int | None = None

    is_duplicate: bool = False
    duplicate_of: str | None = None

    snippet: str | None = None


@dataclass(slots=True)
class SourceCollection:
    """一次回答对应的完整信源采集结果。"""

    status: SourceCollectionStatus = SourceCollectionStatus.NOT_APPLICABLE

    declared_count: int = 0
    captured_count: int = 0
    unique_count: int = 0

    coverage_ratio: float = 0.0

    sources: list[GeoSource] = field(default_factory=list)


@dataclass(slots=True)
class TimingInfo:
    """采集任务关键时间信息。"""

    started_at: str | None = None
    submitted_at: str | None = None
    finished_at: str | None = None
    answer_status_at: str | None = None

    elapsed_seconds: float | None = None


@dataclass(slots=True)
class ArtifactInfo:
    """采集过程保存的证据文件。"""
    screenshot_path: str | None = None
    page_test_path: str | None = None
    raw_html_path: str | None = None
    debug_path: str | None = None


@dataclass(slots=True)
class ValidationIssue:
    """单条数据质量问题。"""

    code: str
    message: str
    severity: ValidationSeverity


@dataclass(slots=True)
class ValidationResult:
    """一次采集结果的Validation 结果。"""
    status: ValidationStatus
    issues: list[ValidationIssue] = field(default_factory=list)
    is_complete: bool = False


@dataclass(slots=True)
class FailureInfo:
    """采集失败信息。"""
    type: FailureType
    message: str

    retryable: bool = False


@dataclass(slots=True)
class GeoRunResult:
    """单个 GEO 任务的完整采集结果。"""
    provider: str

    run_id: str
    task: GeoTask

    batch_id: str | None = None

    answer_text: str = ""

    sources: SourceCollection = field(default_factory=SourceCollection)

    timing: TimingInfo = field(default_factory=TimingInfo)

    artifacts: ArtifactInfo = field(default_factory=ArtifactInfo)

    validation: ValidationResult | None = None

    failure: FailureInfo | None = None

    status: TaskStatus = TaskStatus.PENDING
