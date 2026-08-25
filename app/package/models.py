from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class PackageCapabilities:
    """geo_package_v1 支持能力声明。"""

    supports_sources: bool = True
    supports_multiple_modes: bool = True
    supports_screenshot: bool = True


@dataclass(frozen=True, slots=True)
class PackageManifest:
    """manifest.json 数据结构。"""

    schema_version: str
    geo_batch_version: str

    platform_code: str
    platform_name: str

    product_id: str
    product_name: str

    batch_id: str

    collector_version: str
    generator_version: str

    status: str

    started_at: str | None
    finished_at: str | None

    created_at: str | None
    completed_at: str | None

    source_system: str
    source_export_type: str

    expected_tasks: int
    completed_tasks: int
    valid_tasks: int
    failed_tasks: int

    collection_modes: list[str]

    task_count: int
    answer_count: int
    source_count: int

    capabilities: PackageCapabilities = field(
        default_factory=PackageCapabilities
    )


@dataclass(frozen=True, slots=True)
class PackageTaskRow:
    """tasks.jsonl 单行结构。"""

    task_id: str
    batch_id: str
    platform_code: str

    question_id: str
    question: str
    mode_code: str

    task_status: str

    error_code: str | None
    error_message: str | None

    created_at: str | None
    finished_at: str | None

    elapsed_seconds: float | None


@dataclass(frozen=True, slots=True)
class PackageAnswerRow:
    """answers.jsonl 单行结构。"""

    answer_id: str
    task_id: str
    batch_id: str

    platform_code: str
    product_id: str

    question_id: str
    mode_code: str
    question_text: str

    answer_text_raw: str
    answer_text_clean: str

    acquisition_status: str
    validation_status: str

    is_complete: bool

    source_collection_status: str
    source_count_raw: int

    screenshot_path: str | None
    collected_at: str | None

    platform_meta_json: dict[str, Any]


@dataclass(frozen=True, slots=True)
class PackageSourceRow:
    """sources.jsonl 单行结构。"""

    answer_id: str
    task_id: str
    question_id: str
    mode_code: str

    source_order: int

    source_title_raw: str | None
    source_site_name_raw: str | None

    source_url_raw: str | None
    resolved_url: str | None
    raw_href: str | None
    domain: str | None

    source_snippet: str | None

    is_duplicate_in_answer: bool

    occurrence_index: int
    search_round: int | None

    source_status: str
    is_valid: bool

    normalized_source_url_raw: str | None

    occurrence_id: str


@dataclass(frozen=True, slots=True)
class PackageChecksums:
    """checksums.json 数据结构。"""

    files: dict[str, str]


@dataclass(frozen=True, slots=True)
class PackageReadResult:
    """
    geo_package 读取结果。
    """

    manifest: PackageManifest

    tasks: list[PackageTaskRow]

    answers: list[PackageAnswerRow]

    sources: list[PackageSourceRow]

    checksums: PackageChecksums
