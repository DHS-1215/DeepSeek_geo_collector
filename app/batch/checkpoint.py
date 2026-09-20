from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.enums import (
    FailureType,
    GeoMode,
    SourceCollectionStatus,
    TaskStatus,
    ValidationSeverity,
    ValidationStatus,
)
from app.core.models import (
    ArtifactInfo,
    FailureInfo,
    GeoRunResult,
    GeoSource,
    GeoTask,
    SourceCollection,
    TimingInfo,
    ValidationIssue,
    ValidationResult,
)
from app.package.serialization import (
    json_bytes,
    jsonl_bytes,
)


CHECKPOINT_VERSION = 1


@dataclass(slots=True)
class BatchCheckpoint:
    """
    一个 Batch 的断点进度信息。

    results.jsonl 只保存已经成功完成的任务结果。
    failed / pending 任务在下次恢复时重新执行。
    """

    version: int
    batch_id: str
    status: str
    total_count: int
    successful_count: int
    successful_task_ids: list[str]
    updated_at: str


@dataclass(slots=True)
class CheckpointSnapshot:
    """
    从磁盘恢复出来的一次 Batch 快照。
    """

    checkpoint: BatchCheckpoint
    results: list[GeoRunResult]


def get_checkpoint_dir(
        output_dir: Path,
        batch_id: str,
) -> Path:
    return (
        output_dir
        / "checkpoints"
        / batch_id
    )


def get_checkpoint_path(
        output_dir: Path,
        batch_id: str,
) -> Path:
    return (
        get_checkpoint_dir(
            output_dir,
            batch_id,
        )
        / "checkpoint.json"
    )


def get_results_path(
        output_dir: Path,
        batch_id: str,
) -> Path:
    return (
        get_checkpoint_dir(
            output_dir,
            batch_id,
        )
        / "results.jsonl"
    )


def save_checkpoint(
        *,
        output_dir: Path,
        batch_id: str,
        total_count: int,
        results: list[GeoRunResult],
        status: str = "RUNNING",
) -> BatchCheckpoint:
    """
    保存 Batch 断点。

    只持久化 SUCCESS 任务。

    这样如果某个任务因为网络、页面异常、
    登录失效等原因失败，下次恢复时仍会重新采集。
    """

    successful_results = [
        result
        for result in results
        if result.status == TaskStatus.SUCCESS
    ]

    checkpoint = BatchCheckpoint(
        version=CHECKPOINT_VERSION,
        batch_id=batch_id,
        status=status,
        total_count=total_count,
        successful_count=len(
            successful_results
        ),
        successful_task_ids=[
            result.task.task_id
            for result in successful_results
        ],
        updated_at=(
            datetime.now().isoformat(
                timespec="seconds"
            )
        ),
    )

    directory = get_checkpoint_dir(
        output_dir,
        batch_id,
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    _atomic_write_bytes(
        get_results_path(
            output_dir,
            batch_id,
        ),
        jsonl_bytes(
            successful_results
        ),
    )

    _atomic_write_bytes(
        get_checkpoint_path(
            output_dir,
            batch_id,
        ),
        json_bytes(
            checkpoint
        ),
    )

    return checkpoint


def load_checkpoint(
        *,
        output_dir: Path,
        batch_id: str,
) -> CheckpointSnapshot | None:
    """
    读取一个 Batch 的断点快照。

    checkpoint.json 不存在时返回 None。
    """

    checkpoint_path = (
        get_checkpoint_path(
            output_dir,
            batch_id,
        )
    )

    if not checkpoint_path.is_file():
        return None

    checkpoint_payload = json.loads(
        checkpoint_path.read_text(
            encoding="utf-8"
        )
    )

    checkpoint = BatchCheckpoint(
        version=int(
            checkpoint_payload["version"]
        ),
        batch_id=str(
            checkpoint_payload["batch_id"]
        ),
        status=str(
            checkpoint_payload["status"]
        ),
        total_count=int(
            checkpoint_payload["total_count"]
        ),
        successful_count=int(
            checkpoint_payload[
                "successful_count"
            ]
        ),
        successful_task_ids=[
            str(item)
            for item in checkpoint_payload[
                "successful_task_ids"
            ]
        ],
        updated_at=str(
            checkpoint_payload[
                "updated_at"
            ]
        ),
    )

    if (
            checkpoint.version
            != CHECKPOINT_VERSION
    ):
        raise ValueError(
            "Unsupported checkpoint version: "
            f"{checkpoint.version}"
        )

    results_path = get_results_path(
        output_dir,
        batch_id,
    )

    results: list[GeoRunResult] = []

    if results_path.is_file():
        for line in (
                results_path
                .read_text(
                    encoding="utf-8"
                )
                .splitlines()
        ):
            line = line.strip()

            if not line:
                continue

            payload = json.loads(
                line
            )

            results.append(
                deserialize_run_result(
                    payload
                )
            )

    return CheckpointSnapshot(
        checkpoint=checkpoint,
        results=results,
    )


def deserialize_run_result(
        payload: dict[str, Any],
) -> GeoRunResult:
    """
    将 results.jsonl 中的一条记录
    恢复为 GeoRunResult。
    """

    task_payload = payload["task"]

    task = GeoTask(
        task_id=str(
            task_payload["task_id"]
        ),
        question_id=str(
            task_payload["question_id"]
        ),
        question=str(
            task_payload["question"]
        ),
        mode=GeoMode(
            task_payload["mode"]
        ),
    )

    source_payload = payload.get(
        "sources"
    ) or {}

    sources = SourceCollection(
        status=SourceCollectionStatus(
            source_payload.get(
                "status",
                SourceCollectionStatus
                .NOT_APPLICABLE
                .value,
            )
        ),
        declared_count=int(
            source_payload.get(
                "declared_count",
                0,
            )
        ),
        captured_count=int(
            source_payload.get(
                "captured_count",
                0,
            )
        ),
        unique_count=int(
            source_payload.get(
                "unique_count",
                0,
            )
        ),
        coverage_ratio=float(
            source_payload.get(
                "coverage_ratio",
                0.0,
            )
        ),
        sources=[
            _deserialize_source(item)
            for item in (
                source_payload.get(
                    "sources",
                    [],
                )
            )
        ],
    )

    timing_payload = (
        payload.get("timing")
        or {}
    )

    timing = TimingInfo(
        started_at=timing_payload.get(
            "started_at"
        ),
        submitted_at=timing_payload.get(
            "submitted_at"
        ),
        finished_at=timing_payload.get(
            "finished_at"
        ),
        answer_status_at=(
            timing_payload.get(
                "answer_status_at"
            )
        ),
        elapsed_seconds=(
            timing_payload.get(
                "elapsed_seconds"
            )
        ),
    )

    artifact_payload = (
        payload.get("artifacts")
        or {}
    )

    artifacts = ArtifactInfo(
        screenshot_path=(
            artifact_payload.get(
                "screenshot_path"
            )
        ),
        page_test_path=(
            artifact_payload.get(
                "page_test_path"
            )
        ),
        raw_html_path=(
            artifact_payload.get(
                "raw_html_path"
            )
        ),
        debug_path=(
            artifact_payload.get(
                "debug_path"
            )
        ),
    )

    validation = _deserialize_validation(
        payload.get("validation")
    )

    failure = _deserialize_failure(
        payload.get("failure")
    )

    return GeoRunResult(
        provider=str(
            payload["provider"]
        ),
        run_id=str(
            payload["run_id"]
        ),
        task=task,
        batch_id=payload.get(
            "batch_id"
        ),
        answer_text_raw=str(
            payload.get(
                "answer_text_raw",
                "",
            )
        ),
        answer_text_clean=str(
            payload.get(
                "answer_text_clean",
                "",
            )
        ),
        sources=sources,
        timing=timing,
        artifacts=artifacts,
        validation=validation,
        failure=failure,
        status=TaskStatus(
            payload.get(
                "status",
                TaskStatus.PENDING.value,
            )
        ),
    )


def _deserialize_source(
        payload: dict[str, Any],
) -> GeoSource:
    return GeoSource(
        occurrence_id=str(
            payload["occurrence_id"]
        ),
        order=int(
            payload["order"]
        ),
        title=payload.get("title"),
        clean_title=payload.get(
            "clean_title"
        ),
        site_name=payload.get(
            "site_name"
        ),
        raw_href=payload.get(
            "raw_href"
        ),
        resolved_url=payload.get(
            "resolved_url"
        ),
        domain=payload.get(
            "domain"
        ),
        source_round=payload.get(
            "source_round"
        ),
        is_duplicate=bool(
            payload.get(
                "is_duplicate",
                False,
            )
        ),
        duplicate_of=payload.get(
            "duplicate_of"
        ),
        snippet=payload.get(
            "snippet"
        ),
    )


def _deserialize_validation(
        payload: dict[str, Any] | None,
) -> ValidationResult | None:
    if payload is None:
        return None

    issues = [
        ValidationIssue(
            code=str(
                item["code"]
            ),
            message=str(
                item["message"]
            ),
            severity=ValidationSeverity(
                item["severity"]
            ),
        )
        for item in payload.get(
            "issues",
            [],
        )
    ]

    return ValidationResult(
        status=ValidationStatus(
            payload["status"]
        ),
        issues=issues,
        is_complete=bool(
            payload.get(
                "is_complete",
                False,
            )
        ),
    )


def _deserialize_failure(
        payload: dict[str, Any] | None,
) -> FailureInfo | None:
    if payload is None:
        return None

    return FailureInfo(
        type=FailureType(
            payload["type"]
        ),
        message=str(
            payload["message"]
        ),
        retryable=bool(
            payload.get(
                "retryable",
                False,
            )
        ),
    )


def _atomic_write_bytes(
        path: Path,
        data: bytes,
) -> None:
    """
    先写临时文件，再原子替换正式文件。

    尽量避免程序异常退出时留下半截 JSON。
    """

    temporary_path = (
        path.parent
        / f"{path.name}.tmp"
    )

    temporary_path.write_bytes(
        data
    )

    temporary_path.replace(
        path
    )
