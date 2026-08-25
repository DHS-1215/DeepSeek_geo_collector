import json
import zipfile
from pathlib import Path
from typing import Any

from app.package.models import (
    PackageAnswerRow,
    PackageChecksums,
    PackageManifest,
    PackageReadResult,
    PackageSourceRow,
    PackageTaskRow,
)


REQUIRED_FILES = {
    "manifest.json",
    "tasks.jsonl",
    "answers.jsonl",
    "sources.jsonl",
    "checksums.json",
}


def read_geo_package(
        package_path: Path,
) -> PackageReadResult:
    """
    读取 geo_package_v1 ZIP。
    """

    with zipfile.ZipFile(
            package_path,
            mode="r",
    ) as archive:

        names = set(
            archive.namelist()
        )

        missing = (
            REQUIRED_FILES
            -
            names
        )

        if missing:
            raise ValueError(
                "missing package files: "
                f"{sorted(missing)}"
            )

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

    return PackageReadResult(
        manifest=PackageManifest(
            **manifest
        ),
        tasks=[
            PackageTaskRow(**item)
            for item in tasks
        ],
        answers=[
            PackageAnswerRow(**item)
            for item in answers
        ],
        sources=[
            PackageSourceRow(**item)
            for item in sources
        ],
        checksums=PackageChecksums(
            **checksums
        ),
    )


def _read_json(
        archive: zipfile.ZipFile,
        filename: str,
) -> dict[str, Any]:

    raw = archive.read(
        filename
    )

    return json.loads(
        raw.decode("utf-8")
    )


def _read_jsonl(
        archive: zipfile.ZipFile,
        filename: str,
) -> list[dict[str, Any]]:

    raw = archive.read(
        filename
    )

    rows = []

    for line in raw.decode(
            "utf-8"
    ).splitlines():

        if not line.strip():
            continue

        rows.append(
            json.loads(line)
        )

    return rows