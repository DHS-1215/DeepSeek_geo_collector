from pathlib import Path

from app.core.enums import (
    GeoMode,
    TaskStatus,
    ValidationStatus,
)
from app.core.models import (
    ArtifactInfo,
    GeoRunResult,
    GeoTask,
    ValidationResult,
)
from app.package.exporter import export_geo_package
from app.package.verifier import verify_geo_package


def test_verify_geo_package(
        tmp_path: Path,
) -> None:
    task = GeoTask(
        task_id="Q001_quick",
        question_id="Q001",
        question="测试问题",
        mode=GeoMode.QUICK,
    )

    result = GeoRunResult(
        provider="deepseek",
        run_id="run_001",
        task=task,
        answer_text_raw="测试回答。",
        answer_text_clean="测试回答。",
        validation=ValidationResult(
            status=ValidationStatus.PASS,
        ),
        status=TaskStatus.SUCCESS,
    )

    package_path = export_geo_package(
        batch_id="batch_verify_001",
        results=[result],
        output_dir=tmp_path,
        product_id="hongmao_yaojiu",
        product_name="鸿茅药酒",
    )

    verify_geo_package(package_path)


import zipfile

import pytest

from app.package.verifier import (
    PackageVerificationError,
)


def test_verify_rejects_tampered_package(
        tmp_path: Path,
) -> None:
    task = GeoTask(
        task_id="Q002_quick",
        question_id="Q002",
        question="校验测试",
        mode=GeoMode.QUICK,
    )

    result = GeoRunResult(
        provider="deepseek",
        run_id="run_002",
        task=task,
        answer_text_raw="测试回答。",
        answer_text_clean="测试回答。",
        validation=ValidationResult(
            status=ValidationStatus.PASS,
        ),
        status=TaskStatus.SUCCESS,
    )

    package_path = export_geo_package(
        batch_id="batch_verify_002",
        results=[result],
        output_dir=tmp_path,
        product_id="hongmao_yaojiu",
        product_name="鸿茅药酒",
    )

    with pytest.warns(
            UserWarning,
            match="Duplicate name",
    ):
        with zipfile.ZipFile(
                package_path,
                mode="a",
        ) as archive:
            archive.writestr(
                "tasks.jsonl",
                b'{"tampered":true}\n',
            )

    with pytest.raises(
            PackageVerificationError,
            match="Checksum mismatch",
    ):
        verify_geo_package(package_path)



def test_verify_geo_package_with_screenshot(
        tmp_path: Path,
) -> None:
    screenshot = (
        tmp_path / "screenshot.png"
    )
    screenshot.write_bytes(
        b"fake-png"
    )

    task = GeoTask(
        task_id="Q003_quick",
        question_id="Q003",
        question="screenshot verify test",
        mode=GeoMode.QUICK,
    )

    result = GeoRunResult(
        provider="deepseek",
        run_id="run_screenshot_verify",
        task=task,
        answer_text_raw="answer",
        answer_text_clean="answer",
        artifacts=ArtifactInfo(
            screenshot_path=str(
                screenshot
            )
        ),
        validation=ValidationResult(
            status=ValidationStatus.PASS,
        ),
        status=TaskStatus.SUCCESS,
    )

    package_path = export_geo_package(
        batch_id="batch_screenshot_verify",
        results=[result],
        output_dir=tmp_path,
        product_id="test_product",
        product_name="test product",
    )

    verify_geo_package(
        package_path
    )



def test_verify_rejects_missing_screenshot_checksum(
        tmp_path: Path,
) -> None:
    import json

    screenshot = (
        tmp_path / "missing_checksum.png"
    )
    screenshot.write_bytes(
        b"fake-png"
    )

    task = GeoTask(
        task_id="Q004_quick",
        question_id="Q004",
        question="missing screenshot checksum test",
        mode=GeoMode.QUICK,
    )

    result = GeoRunResult(
        provider="deepseek",
        run_id="run_missing_checksum",
        task=task,
        answer_text_raw="answer",
        answer_text_clean="answer",
        artifacts=ArtifactInfo(
            screenshot_path=str(
                screenshot
            )
        ),
        validation=ValidationResult(
            status=ValidationStatus.PASS,
        ),
        status=TaskStatus.SUCCESS,
    )

    package_path = export_geo_package(
        batch_id="batch_missing_checksum",
        results=[result],
        output_dir=tmp_path,
        product_id="test_product",
        product_name="test product",
    )

    with zipfile.ZipFile(
            package_path,
            "r",
    ) as archive:
        entries = {
            info.filename: (
                archive.read(
                    info.filename
                )
                if not info.is_dir()
                else b""
            )
            for info in archive.infolist()
        }

    checksums = json.loads(
        entries["checksums.json"]
    )

    screenshot_name = (
        "screenshots/"
        "Q004_quick.png"
    )

    checksums["files"].pop(
        screenshot_name
    )

    entries["checksums.json"] = (
        json.dumps(
            checksums,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    )

    tampered_path = (
        tmp_path
        / "missing_screenshot_checksum.zip"
    )

    with zipfile.ZipFile(
            tampered_path,
            "w",
            compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        for name, content in entries.items():
            if name.endswith("/"):
                archive.writestr(
                    name,
                    b"",
                )
            else:
                archive.writestr(
                    name,
                    content,
                )

    with pytest.raises(
            PackageVerificationError,
            match="Unexpected checksum file set",
    ):
        verify_geo_package(
            tampered_path
        )
