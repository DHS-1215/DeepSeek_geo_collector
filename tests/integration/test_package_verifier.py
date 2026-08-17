from pathlib import Path

from app.core.enums import (
    GeoMode,
    TaskStatus,
    ValidationStatus,
)
from app.core.models import (
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
        answer_text="测试回答。",
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
        answer_text="测试回答。",
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
