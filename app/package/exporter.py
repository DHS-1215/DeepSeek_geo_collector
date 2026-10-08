import re
import zipfile
from pathlib import Path
from typing import Any

from app.core.enums import GeoMode, ValidationSeverity
from app.core.models import GeoRunResult
from app.package.checksum import build_checksums
from app.package.constants import (
    CHECKSUM_DATA_FILES,
    DEFAULT_PLATFORM_CODE,
    DEFAULT_PLATFORM_NAME,
    DEFAULT_SOURCE_EXPORT_TYPE,
    DEFAULT_SOURCE_SYSTEM,
    GENERATOR_VERSION,
    GEO_BATCH_VERSION,
    PACKAGE_SCHEMA_VERSION,
)
from app.package.mapping import (
    answer_is_complete,
    map_acquisition_status,
    map_source_status,
    map_task_status,
    map_validation_status,
)
from app.package.models import (
    PackageAnswerRow,
    PackageCapabilities,
    PackageChecksums,
    PackageManifest,
    PackageSourceRow,
    PackageTaskRow,
)
from app.package.serialization import json_bytes, jsonl_bytes
from app.package.source_utils import (
    canonicalize_url,
    finalize_source_rows,
)


def export_geo_package(
        *,
        batch_id: str,
        results: list[GeoRunResult],
        output_dir: Path,
        product_id: str,
        product_name: str,
        platform_code: str = DEFAULT_PLATFORM_CODE,
        platform_name: str = DEFAULT_PLATFORM_NAME,
) -> Path:
    """将一批 GeoRunResult 导出为 geo_package_v1 ZIP。"""

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    task_rows: list[PackageTaskRow] = []
    answer_rows: list[PackageAnswerRow] = []

    raw_source_rows: list[dict[str, Any]] = []

    screenshot_files: list[
        tuple[Path, str]
    ] = []

    for result in results:
        task = result.task

        task_status = map_task_status(
            result.status
        )

        validation_status = (
            map_validation_status(
                result.validation
            )
        )

        source_status = map_source_status(
            task.mode,
            result.sources,
        )

        answer_id = (
            f"{batch_id}_{task.task_id}"
        )

        task_rows.append(
            PackageTaskRow(
                task_id=task.task_id,
                batch_id=batch_id,
                platform_code=platform_code,
                question_id=task.question_id,
                question=task.question,
                mode_code=task.mode.value,
                task_status=task_status,

                # 为保持当前 geo_package_v1 行为，
                # 暂时不扩展 error_code。
                error_code=None,

                error_message=(
                    result.failure.message
                    if result.failure
                    else None
                ),

                created_at=(
                    result.timing.started_at
                ),
                finished_at=(
                    result.timing.finished_at
                ),
                elapsed_seconds=(
                    result.timing.elapsed_seconds
                ),
            )
        )

        screenshot_path = (
            _relative_screenshot_path(
                task.task_id,
                result,
            )
        )

        if screenshot_path is not None:
            source_path = Path(
                result.artifacts.screenshot_path
                or ""
            )

            screenshot_files.append(
                (
                    source_path,
                    screenshot_path,
                )
            )

        answer_rows.append(
            PackageAnswerRow(
                answer_id=answer_id,
                task_id=task.task_id,
                batch_id=batch_id,
                platform_code=platform_code,
                product_id=product_id,

                question_id=task.question_id,
                mode_code=task.mode.value,
                question_text=task.question,

                answer_text_raw=(
                    result.answer_text_raw
                ),
                answer_text_clean=(
                    result.answer_text_clean
                ),

                acquisition_status=(
                    map_acquisition_status(
                        result
                    )
                ),
                validation_status=(
                    validation_status
                ),
                is_complete=(
                    answer_is_complete(
                        result
                    )
                ),

                source_collection_status=(
                    source_status
                ),

                source_count_raw=(
                    len(result.sources.sources)
                ),

                screenshot_path=(
                    screenshot_path
                ),

                collected_at=(
                    result.timing.finished_at
                ),

                platform_meta_json=(
                    _build_platform_meta(
                        result
                    )
                ),
            )
        )


        seen_canonical_urls: set[str] = (
            set()
        )

        source_order_by_url: dict[str, int] = {}
        next_source_order = 1

        for index, source in enumerate(
                result.sources.sources,
                start=1,
        ):
            url = str(
                source.resolved_url
                or source.raw_href
                or ""
            ).strip()

            if not url:
                continue

            canonical_url = (
                canonicalize_url(url)
            )

            duplicate_in_answer = (
                    canonical_url
                    in seen_canonical_urls
            )

            seen_canonical_urls.add(
                canonical_url
            )

            source_order = (
                source_order_by_url.get(
                    canonical_url
                )
            )

            if source_order is None:
                source_order = (
                    next_source_order
                )

                source_order_by_url[
                    canonical_url
                ] = source_order

                next_source_order += 1

            raw_source_rows.append(
                {
                    "answer_id": answer_id,
                    "task_id": task.task_id,
                    "question_id": (
                        task.question_id
                    ),
                    "mode_code": (
                        task.mode.value
                    ),
                    "source_order": (
                        int(source_order)
                    ),
                    "source_title_raw": (
                            source.clean_title
                            or source.title
                    ),
                    "source_site_name_raw": (
                            source.site_name
                            or source.domain
                    ),
                    "source_url_raw": url,
                    "resolved_url": (
                        source.resolved_url
                    ),
                    "raw_href": (
                        source.raw_href
                    ),
                    "domain": (
                        source.domain
                    ),
                    "source_snippet": (
                        source.snippet
                    ),
                    "is_duplicate_in_answer": bool(
                        source.is_duplicate
                        or source.duplicate_of
                        or duplicate_in_answer
                    ),
                    "occurrence_index": (
                        index
                    ),
                    "occurrence_id": (
                        source.occurrence_id
                    ),
                    "search_round": (
                        source.source_round
                    ),
                    "source_status": (
                        "success"
                    ),
                    "is_valid": True,
                }
            )

    finalized_source_dicts, _ = (
        finalize_source_rows(
            batch_id,
            raw_source_rows,
        )
    )

    source_rows = [
        PackageSourceRow(**row)
        for row in finalized_source_dicts
    ]

    manifest = _build_manifest(
        batch_id=batch_id,
        task_rows=task_rows,
        answer_rows=answer_rows,
        source_rows=source_rows,
        platform_code=platform_code,
        platform_name=platform_name,
        product_id=product_id,
        product_name=product_name,
    )

    package_files = _build_package_files(
        manifest=manifest,
        tasks=task_rows,
        answers=answer_rows,
        sources=source_rows,
    )

    package_path = (
            output_dir
            / (
                f"geo_package_"
                f"{platform_code}_"
                f"{batch_id}.zip"
            )
    )

    _write_zip(
        package_path=package_path,
        package_files=package_files,
        screenshot_files=(
            screenshot_files
        ),
    )

    return package_path


def _build_manifest(
        *,
        batch_id: str,
        task_rows: list[PackageTaskRow],
        answer_rows: list[PackageAnswerRow],
        source_rows: list[PackageSourceRow],
        platform_code: str,
        platform_name: str,
        product_id: str,
        product_name: str,
) -> PackageManifest:
    """构造 manifest.json。"""

    started_at = _min_value(
        row.created_at
        for row in task_rows
    )

    finished_at = _max_value(
        row.finished_at
        for row in task_rows
    )

    all_success = all(
        row.task_status == "success"
        for row in task_rows
    )

    completed_tasks = sum(
        1
        for row in task_rows
        if row.task_status
        in {
            "success",
            "failed",
        }
    )

    valid_tasks = sum(
        1
        for row in answer_rows
        if (
                row.is_complete
                and row.validation_status
                in {
                    "PASS",
                    "PASS_WITH_WARNINGS",
                }
        )
    )

    failed_tasks = sum(
        1
        for row in task_rows
        if row.task_status == "failed"
    )

    collection_modes = sorted(
        {
            row.mode_code
            for row in task_rows
        }
    )

    return PackageManifest(
        schema_version=(
            PACKAGE_SCHEMA_VERSION
        ),
        geo_batch_version=(
            GEO_BATCH_VERSION
        ),

        platform_code=platform_code,
        platform_name=platform_name,

        product_id=product_id,
        product_name=product_name,

        batch_id=batch_id,

        collector_version=(
            GENERATOR_VERSION
        ),
        generator_version=(
            GENERATOR_VERSION
        ),

        status=(
            "PASS"
            if all_success
            else "PASS_WITH_WARNINGS"
        ),

        started_at=started_at,
        finished_at=finished_at,

        created_at=started_at,
        completed_at=finished_at,

        source_system=(
            DEFAULT_SOURCE_SYSTEM
        ),
        source_export_type=(
            DEFAULT_SOURCE_EXPORT_TYPE
        ),

        expected_tasks=len(
            task_rows
        ),
        completed_tasks=(
            completed_tasks
        ),
        valid_tasks=valid_tasks,
        failed_tasks=failed_tasks,

        collection_modes=(
            collection_modes
        ),

        task_count=len(
            task_rows
        ),
        answer_count=len(
            answer_rows
        ),
        source_count=len(
            source_rows
        ),

        capabilities=(
            PackageCapabilities()
        ),
    )


def _build_package_files(
        *,
        manifest: PackageManifest,
        tasks: list[PackageTaskRow],
        answers: list[PackageAnswerRow],
        sources: list[PackageSourceRow],
) -> dict[str, bytes]:
    """生成 ZIP 中的固定数据文件。"""

    data_files = {
        "manifest.json": (
            json_bytes(manifest)
        ),
        "tasks.jsonl": (
            jsonl_bytes(tasks)
        ),
        "answers.jsonl": (
            jsonl_bytes(answers)
        ),
        "sources.jsonl": (
            jsonl_bytes(sources)
        ),
    }

    checksum_input = {
        filename: data_files[
            filename
        ]
        for filename
        in CHECKSUM_DATA_FILES
    }

    checksums = PackageChecksums(
        files=build_checksums(
            checksum_input
        )
    )

    return {
        **data_files,
        "checksums.json": (
            json_bytes(checksums)
        ),
    }


def _write_zip(
        *,
        package_path: Path,
        package_files: dict[str, bytes],
        screenshot_files: list[
            tuple[Path, str]
        ],
) -> None:
    """写入最终 geo_package_v1 ZIP。"""

    package_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with zipfile.ZipFile(
            package_path,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        # 固定协议文件顺序。
        for filename in (
                "manifest.json",
                "tasks.jsonl",
                "answers.jsonl",
                "sources.jsonl",
                "checksums.json",
        ):
            archive.writestr(
                filename,
                package_files[filename],
            )

        existing_screenshots = [
            (
                source_path,
                archive_path,
            )
            for source_path, archive_path
            in screenshot_files
            if source_path.exists()
        ]

        if existing_screenshots:
            for (
                    source_path,
                    archive_path,
            ) in sorted(
                existing_screenshots,
                key=lambda item: item[1],
            ):
                archive.write(
                    source_path,
                    archive_path,
                )
        else:
            archive.writestr(
                "screenshots/",
                b"",
            )


def _relative_screenshot_path(
        task_id: str,
        result: GeoRunResult,
) -> str | None:
    """生成 screenshot 在 ZIP 内的相对路径。"""

    raw_path = (
        result.artifacts.screenshot_path
    )

    if not raw_path:
        return None

    screenshot = Path(raw_path)

    if not screenshot.exists():
        return None

    return (
        f"screenshots/"
        f"{_safe_name(task_id)}.png"
    )


def _safe_name(value: str) -> str:
    """生成 ZIP 内安全文件名。"""

    normalized = re.sub(
        r"[^A-Za-z0-9._-]+",
        "_",
        value,
    ).strip("_")

    return normalized or "item"


def _build_platform_meta(
        result: GeoRunResult,
) -> dict[str, Any]:
    """构造 answers.jsonl.platform_meta_json。"""

    validation = result.validation

    warnings: list[str] = []
    failed_rules: list[str] = []

    if validation is not None:
        for issue in validation.issues:
            if (
                    issue.severity
                    == ValidationSeverity.WARNING
            ):
                warnings.append(
                    issue.code
                )

            elif (
                    issue.severity
                    == ValidationSeverity.ERROR
            ):
                failed_rules.append(
                    issue.code
                )

    search_round_count = len(
        {
            source.source_round
            for source
            in result.sources.sources
            if source.source_round
               is not None
        }
    )

    return {
        "collector_task": {
            "run_id": (
                result.run_id
            ),
            "answer_length": len(
                result.answer_text_raw
            ),
            "source_count": len(
                result.sources.sources
            ),
            "source_collection_status": (
                result.sources.status.value
            ),
        },
        "collector_result": {
            "extraction_method": None,
            "page_url": None,
            "created_at": (
                result.timing.started_at
            ),
            "finished_at": (
                result.timing.finished_at
            ),
            "elapsed_seconds": (
                result.timing.elapsed_seconds
            ),
        },
        "collector_validation": {
            "status": (
                validation.status.value
                if validation
                else None
            ),
            "warnings": warnings,
            "failed_rules": (
                failed_rules
            ),
            "extraction_method": None,
        },
        "collector_source": {
            "status": (
                result.sources.status.value
            ),
            "declared_reference_count": (
                result.sources.declared_count
            ),
            "occurrence_count": (
                result.sources.captured_count
            ),
            "unique_source_count": (
                result.sources.unique_count
            ),
            "search_round_count": (
                search_round_count
            ),
        },
        "collector_evidence": {
            "mention_result": None,
            "sentiment_result": None,
        },
    }


def _min_value(
        values: Any,
) -> str | None:
    present = sorted(
        str(value)
        for value in values
        if value
    )

    return (
        present[0]
        if present
        else None
    )


def _max_value(
        values: Any,
) -> str | None:
    present = sorted(
        str(value)
        for value in values
        if value
    )

    return (
        present[-1]
        if present
        else None
    )
