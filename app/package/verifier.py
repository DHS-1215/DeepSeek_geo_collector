import hashlib
import json
import zipfile
from pathlib import PurePosixPath

from app.package.constants import (
    GEO_BATCH_VERSION,
    PACKAGE_SCHEMA_VERSION,
    REQUIRED_PACKAGE_FILES,
)


class PackageVerificationError(ValueError):
    """geo_package_v1 校验失败。"""


def verify_geo_package(package_path) -> None:
    """严格校验 DeepSeek GEO Package。

    校验成功时正常返回；
    校验失败时抛出 PackageVerificationError。
    """

    if not package_path.exists():
        raise PackageVerificationError(
            f"Package does not exist: {package_path}"
        )

    with zipfile.ZipFile(package_path) as archive:
        names = archive.namelist()

        _verify_safe_paths(names)
        _verify_required_files(names)

        manifest = _read_json(
            archive,
            "manifest.json",
        )

        tasks = _read_jsonl(
            archive,
            "tasks.jsonl",
        )

        answers = _read_jsonl(
            archive,
            "answers.jsonl",
        )

        sources = _read_jsonl(
            archive,
            "sources.jsonl",
        )

        checksums = _read_json(
            archive,
            "checksums.json",
        )

        _verify_versions(manifest)

        _verify_checksums(
            archive,
            checksums,
        )

        _verify_unique_ids(
            tasks,
            answers,
            sources,
        )

        _verify_references(
            tasks,
            answers,
            sources,
        )

        _verify_screenshots(
            names,
            answers,
        )


def _verify_safe_paths(
        names: list[str],
) -> None:
    for name in names:
        path = PurePosixPath(name)

        if path.is_absolute():
            raise PackageVerificationError(
                f"Absolute path is not allowed: {name}"
            )

        if ":" in name:
            raise PackageVerificationError(
                f"Unsafe path contains colon: {name}"
            )

        if ".." in path.parts:
            raise PackageVerificationError(
                f"Unsafe path traversal: {name}"
            )


def _verify_required_files(
        names: list[str],
) -> None:
    present = set(names)

    missing = [
        filename
        for filename in REQUIRED_PACKAGE_FILES
        if filename not in present
    ]

    if missing:
        raise PackageVerificationError(
            f"Missing required package files: {missing}"
        )


def _verify_versions(
        manifest: dict,
) -> None:
    if (
            manifest.get("schema_version")
            != PACKAGE_SCHEMA_VERSION
    ):
        raise PackageVerificationError(
            "Invalid schema_version: "
            f"{manifest.get('schema_version')!r}"
        )

    if (
            manifest.get("geo_batch_version")
            != GEO_BATCH_VERSION
    ):
        raise PackageVerificationError(
            "Invalid geo_batch_version: "
            f"{manifest.get('geo_batch_version')!r}"
        )


def _verify_checksums(
        archive: zipfile.ZipFile,
        checksums: dict,
) -> None:
    files = checksums.get("files")

    if not isinstance(files, dict):
        raise PackageVerificationError(
            "checksums.json.files must be an object"
        )

    expected_files = {
        name
        for name in archive.namelist()
        if (
            name != "checksums.json"
            and not name.endswith("/")
        )
    }

    if set(files) != expected_files:
        raise PackageVerificationError(
            "Unexpected checksum file set: "
            f"{sorted(files)}"
        )

    for filename, expected_hash in files.items():
        content = archive.read(filename)

        actual_hash = hashlib.sha256(
            content
        ).hexdigest()

        if actual_hash != expected_hash:
            raise PackageVerificationError(
                f"Checksum mismatch: {filename}"
            )


def _verify_unique_ids(
        tasks: list[dict],
        answers: list[dict],
        sources: list[dict],
) -> None:
    _ensure_unique_non_empty(
        rows=tasks,
        field="task_id",
    )

    _ensure_unique_non_empty(
        rows=answers,
        field="answer_id",
    )

    _ensure_unique_non_empty(
        rows=sources,
        field="occurrence_id",
    )


def _ensure_unique_non_empty(
        *,
        rows: list[dict],
        field: str,
) -> None:
    seen: set[str] = set()

    for index, row in enumerate(
            rows,
            start=1,
    ):
        value = str(
            row.get(field) or ""
        ).strip()

        if not value:
            raise PackageVerificationError(
                f"{field} is empty at row {index}"
            )

        if value in seen:
            raise PackageVerificationError(
                f"Duplicate {field}: {value}"
            )

        seen.add(value)


def _verify_references(
        tasks: list[dict],
        answers: list[dict],
        sources: list[dict],
) -> None:
    task_ids = {
        str(row["task_id"])
        for row in tasks
    }

    answer_ids = {
        str(row["answer_id"])
        for row in answers
    }

    for answer in answers:
        task_id = str(
            answer.get("task_id") or ""
        )

        if task_id not in task_ids:
            raise PackageVerificationError(
                "Answer references unknown task_id: "
                f"{task_id}"
            )

    for source in sources:
        task_id = str(
            source.get("task_id") or ""
        )

        answer_id = str(
            source.get("answer_id") or ""
        )

        if task_id not in task_ids:
            raise PackageVerificationError(
                "Source references unknown task_id: "
                f"{task_id}"
            )

        if answer_id not in answer_ids:
            raise PackageVerificationError(
                "Source references unknown answer_id: "
                f"{answer_id}"
            )


def _verify_screenshots(
        names: list[str],
        answers: list[dict],
) -> None:
    present = set(names)

    for answer in answers:
        screenshot_path = (
            answer.get("screenshot_path")
        )

        if not screenshot_path:
            continue

        if screenshot_path not in present:
            raise PackageVerificationError(
                "Missing referenced screenshot: "
                f"{screenshot_path}"
            )


def _read_json(
        archive: zipfile.ZipFile,
        filename: str,
) -> dict:
    try:
        return json.loads(
            archive.read(filename)
        )
    except (
            json.JSONDecodeError,
            UnicodeDecodeError,
    ) as exc:
        raise PackageVerificationError(
            f"Invalid JSON file: {filename}"
        ) from exc


def _read_jsonl(
        archive: zipfile.ZipFile,
        filename: str,
) -> list[dict]:
    try:
        text = archive.read(
            filename
        ).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PackageVerificationError(
            f"Invalid UTF-8 JSONL: {filename}"
        ) from exc

    if not text.strip():
        return []

    rows: list[dict] = []

    for line_no, line in enumerate(
            text.splitlines(),
            start=1,
    ):
        if not line.strip():
            continue

        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise PackageVerificationError(
                f"Invalid JSONL: "
                f"{filename}:{line_no}"
            ) from exc

        if not isinstance(row, dict):
            raise PackageVerificationError(
                f"JSONL row must be object: "
                f"{filename}:{line_no}"
            )

        rows.append(row)

    return rows
