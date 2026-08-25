from pathlib import Path
import pytest
from app.package.models import (
    PackageReadResult,
)
from app.package.reader import (
    read_geo_package,
)


def test_read_manifest(
        tmp_path: Path,
) -> None:
    import json
    import zipfile

    package_path = (
            tmp_path
            / "geo_package.zip"
    )

    manifest = {
        "schema_version": "geo_package_v1",
        "geo_batch_version": "1.0",

        "platform_code": "deepseek",
        "platform_name": "DeepSeek",

        "product_id": "hongmao_yaojiu",
        "product_name": "鸿茅药酒",

        "batch_id": "batch_001",

        "collector_version": "1.0",
        "generator_version": "1.0",

        "status": "PASS",

        "started_at": None,
        "finished_at": None,
        "created_at": None,
        "completed_at": None,

        "source_system": "deepseek",
        "source_export_type": "json",

        "expected_tasks": 1,
        "completed_tasks": 1,
        "valid_tasks": 1,
        "failed_tasks": 0,

        "collection_modes": [
            "quick"
        ],

        "task_count": 1,
        "answer_count": 1,
        "source_count": 0,

        "capabilities": {
            "supports_sources": True,
            "supports_multiple_modes": True,
            "supports_screenshot": True,
        },
    }

    empty_rows = {
        "tasks.jsonl": "",
        "answers.jsonl": "",
        "sources.jsonl": "",
        "checksums.json": json.dumps(
            {
                "files": {}
            }
        ),
    }

    with zipfile.ZipFile(
            package_path,
            "w",
    ) as archive:
        archive.writestr(
            "manifest.json",
            json.dumps(
                manifest,
                ensure_ascii=False,
            ),
        )

        for filename, content in empty_rows.items():
            archive.writestr(
                filename,
                content,
            )

    result = read_geo_package(
        package_path
    )

    assert isinstance(
        result,
        PackageReadResult,
    )

    assert (
            result.manifest.batch_id
            == "batch_001"
    )

    assert (
            result.manifest.product_name
            == "鸿茅药酒"
    )

    assert result.tasks == []

    assert result.answers == []

    assert result.sources == []


import pytest


def test_read_geo_package_missing_file(
        tmp_path: Path,
) -> None:
    import json
    import zipfile

    package_path = (
            tmp_path
            / "broken_package.zip"
    )

    manifest = {
        "schema_version": "geo_package_v1",
        "geo_batch_version": "1.0",

        "platform_code": "deepseek",
        "platform_name": "DeepSeek",

        "product_id": "hongmao_yaojiu",
        "product_name": "鸿茅药酒",

        "batch_id": "batch_001",

        "collector_version": "1.0",
        "generator_version": "1.0",

        "status": "PASS",

        "started_at": None,
        "finished_at": None,
        "created_at": None,
        "completed_at": None,

        "source_system": "deepseek",
        "source_export_type": "json",

        "expected_tasks": 1,
        "completed_tasks": 1,
        "valid_tasks": 1,
        "failed_tasks": 0,

        "collection_modes": [
            "quick"
        ],

        "task_count": 1,
        "answer_count": 1,
        "source_count": 0,

        "capabilities": {
            "supports_sources": True,
            "supports_multiple_modes": True,
            "supports_screenshot": True,
        },
    }

    with zipfile.ZipFile(
            package_path,
            "w",
    ) as archive:
        archive.writestr(
            "manifest.json",
            json.dumps(
                manifest,
                ensure_ascii=False,
            ),
        )

    with pytest.raises(
            ValueError,
            match="missing package files",
    ):
        read_geo_package(
            package_path
        )

def test_read_real_w12_package() -> None:
    from pathlib import Path

    package_path = Path(
        "output/w12_metrics/"
        "geo_package_deepseek_w12_metrics_smoke.zip"
    )

    if not package_path.exists():
        pytest.skip(
            "real W12 package not found"
        )

    result = read_geo_package(
        package_path
    )

    assert (
        result.manifest.product_name
        == "鸿茅药酒"
    )

    assert (
        result.manifest.batch_id
        == "w12_metrics_smoke"
    )

    assert len(result.tasks) == 16

    assert len(result.answers) == 16

    assert (
        result.manifest.answer_count
        == 16
    )
