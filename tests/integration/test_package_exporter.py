import hashlib
import json
import zipfile
from pathlib import Path

from app.core.enums import (
    FailureType,
    GeoMode,
    SourceCollectionStatus,
    TaskStatus,
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
    ValidationResult,
)

from app.package.exporter import (
    export_geo_package,
)


def test_export_single_expert_result(
        tmp_path: Path,
) -> None:
    screenshot = (
            tmp_path / "screenshot.png"
    )

    screenshot.write_bytes(
        b"fake-png"
    )

    task = GeoTask(
        task_id="Q001_expert",
        question_id="Q001",
        question="鸿茅药酒是什么？",
        mode=GeoMode.EXPERT,
    )

    source = GeoSource(
        occurrence_id="R1_S1",
        order=1,
        title="测试来源",
        clean_title="测试来源",
        site_name="example",
        snippet="测试摘要",
        raw_href=(
            "https://example.com/page"
            "?utm_source=test&id=1"
        ),
        resolved_url=(
            "https://example.com/page"
            "?utm_source=test&id=1"
        ),
        domain="example.com",
        source_round=1,
    )

    sources = SourceCollection(
        status=(
            SourceCollectionStatus.SUCCESS
        ),
        declared_count=1,
        captured_count=1,
        unique_count=1,
        coverage_ratio=1.0,
        sources=[source],
    )

    result = GeoRunResult(
        provider="deepseek",
        run_id="run_001",
        batch_id="batch_test_001",
        task=task,
        answer_text_raw="正文-\n2\n。",
        answer_text_clean="正文。",
        sources=sources,
        timing=TimingInfo(
            started_at=(
                "2026-08-14T10:00:00"
            ),
            finished_at=(
                "2026-08-14T10:00:10"
            ),
            elapsed_seconds=10.0,
        ),
        artifacts=ArtifactInfo(
            screenshot_path=str(
                screenshot
            )
        ),
        validation=ValidationResult(
            status=ValidationStatus.PASS,
            is_complete=True,
        ),
        status=TaskStatus.SUCCESS,
    )

    package_path = export_geo_package(
        batch_id="batch_test_001",
        results=[result],
        output_dir=tmp_path,
        product_id="hongmao_yaojiu",
        product_name="鸿茅药酒",
    )

    assert package_path.exists()

    assert package_path.name == (
        "geo_package_deepseek_"
        "batch_test_001.zip"
    )

    with zipfile.ZipFile(
            package_path
    ) as archive:
        names = set(
            archive.namelist()
        )

        assert (
                "manifest.json"
                in names
        )

        assert (
                "tasks.jsonl"
                in names
        )

        assert (
                "answers.jsonl"
                in names
        )

        assert (
                "sources.jsonl"
                in names
        )

        assert (
                "checksums.json"
                in names
        )

        assert (
                "screenshots/"
                "Q001_expert.png"
                in names
        )

        manifest = json.loads(
            archive.read(
                "manifest.json"
            )
        )

        assert (
                manifest["schema_version"]
                == "geo_package_v1"
        )

        assert (
                manifest[
                    "geo_batch_version"
                ]
                == "geo_batch_v1"
        )

        assert (
                manifest["platform_code"]
                == "deepseek"
        )

        assert (
                manifest["batch_id"]
                == "batch_test_001"
        )

        assert (
                manifest["task_count"]
                == 1
        )

        assert (
                manifest["answer_count"]
                == 1
        )

        assert (
                manifest["source_count"]
                == 1
        )

        tasks = _read_jsonl(
            archive.read(
                "tasks.jsonl"
            )
        )

        answers = _read_jsonl(
            archive.read(
                "answers.jsonl"
            )
        )

        sources_rows = _read_jsonl(
            archive.read(
                "sources.jsonl"
            )
        )

        assert len(tasks) == 1
        assert len(answers) == 1
        assert len(sources_rows) == 1

        assert (
                answers[0]["answer_id"]
                == (
                    "batch_test_001_"
                    "Q001_expert"
                )
        )

        assert (
                answers[0][
                    "source_collection_status"
                ]
                == "success"
        )

        assert (
                sources_rows[0][
                    "normalized_source_url_raw"
                ]
                == (
                    "https://example.com/"
                    "page?id=1"
                )
        )

        assert (
            sources_rows[0][
                "occurrence_id"
            ].startswith(
                "batch_test_001_"
                "0001_"
            )
        )

        checksums = json.loads(
            archive.read(
                "checksums.json"
            )
        )

        for filename in (
                "manifest.json",
                "tasks.jsonl",
                "answers.jsonl",
                "sources.jsonl",
        ):
            expected = hashlib.sha256(
                archive.read(filename)
            ).hexdigest()

            assert (
                    checksums[
                        "files"
                    ][filename]
                    == expected
            )


def _read_jsonl(
        content: bytes,
) -> list[dict]:
    text = (
        content
        .decode("utf-8")
        .strip()
    )

    if not text:
        return []

    return [
        json.loads(line)
        for line
        in text.splitlines()
    ]


def test_export_quick_result_without_sources(
        tmp_path: Path,
) -> None:
    task = GeoTask(
        task_id="Q001_quick",
        question_id="Q001",
        question="测试 quick 问题",
        mode=GeoMode.QUICK,
    )

    result = GeoRunResult(
        provider="deepseek",
        run_id="run_quick_001",
        batch_id="batch_quick_001",
        task=task,
        answer_text_raw="正文-\n2\n。",
        answer_text_clean="正文。",
        sources=SourceCollection(
            status=SourceCollectionStatus.NOT_SUPPORTED,
        ),
        timing=TimingInfo(
            started_at="2026-08-17T09:00:00",
            finished_at="2026-08-17T09:00:05",
            elapsed_seconds=5.0,
        ),
        validation=ValidationResult(
            status=ValidationStatus.PASS,
            is_complete=True,
        ),
        status=TaskStatus.SUCCESS,
    )

    package_path = export_geo_package(
        batch_id="batch_quick_001",
        results=[result],
        output_dir=tmp_path,
        product_id="hongmao_yaojiu",
        product_name="鸿茅药酒",
    )

    with zipfile.ZipFile(package_path) as archive:
        answers = _read_jsonl(
            archive.read("answers.jsonl")
        )
        sources = _read_jsonl(
            archive.read("sources.jsonl")
        )

        assert len(answers) == 1

        assert (
                answers[0]["answer_text_raw"]
                == "正文-\n2\n。"
        )

        assert (
                answers[0]["answer_text_clean"]
                == "正文。"
        )

        assert sources == []

        assert (
                answers[0]["source_collection_status"]
                == "not_supported"
        )

        assert answers[0]["source_count_raw"] == 0


def test_export_failed_result(
        tmp_path: Path,
) -> None:
    task = GeoTask(
        task_id="Q002_expert",
        question_id="Q002",
        question="失败测试问题",
        mode=GeoMode.EXPERT,
    )

    result = GeoRunResult(
        provider="deepseek",
        run_id="run_failed_001",
        batch_id="batch_failed_001",
        task=task,
        answer_text_raw="正文-\n2\n。",
        answer_text_clean="正文。",
        failure=FailureInfo(
            type=FailureType.ANSWER_TIMEOUT,
            message="answer timed out",
            retryable=True,
        ),
        validation=ValidationResult(
            status=ValidationStatus.FAIL,
            is_complete=False,
        ),
        status=TaskStatus.FAILED,
    )

    package_path = export_geo_package(
        batch_id="batch_failed_001",
        results=[result],
        output_dir=tmp_path,
        product_id="hongmao_yaojiu",
        product_name="鸿茅药酒",
    )

    with zipfile.ZipFile(package_path) as archive:
        manifest = json.loads(
            archive.read("manifest.json")
        )

        tasks = _read_jsonl(
            archive.read("tasks.jsonl")
        )

        answers = _read_jsonl(
            archive.read("answers.jsonl")
        )

        assert manifest["status"] == "PASS_WITH_WARNINGS"
        assert manifest["failed_tasks"] == 1
        assert manifest["valid_tasks"] == 0

        assert tasks[0]["task_status"] == "failed"
        assert tasks[0]["error_message"] == "answer timed out"

        assert answers[0]["acquisition_status"] == "failed"
        assert answers[0]["is_complete"] is False


def test_export_without_screenshot_creates_empty_screenshot_directory(
        tmp_path: Path,
) -> None:
    task = GeoTask(
        task_id="Q003_quick",
        question_id="Q003",
        question="无截图测试",
        mode=GeoMode.QUICK,
    )

    result = GeoRunResult(
        provider="deepseek",
        run_id="run_no_screenshot",
        task=task,
        answer_text_raw="正文-\n2\n。",
        answer_text_clean="正文。",
        validation=ValidationResult(
            status=ValidationStatus.PASS,
        ),
        status=TaskStatus.SUCCESS,
    )

    package_path = export_geo_package(
        batch_id="batch_no_screenshot",
        results=[result],
        output_dir=tmp_path,
        product_id="hongmao_yaojiu",
        product_name="鸿茅药酒",
    )

    with zipfile.ZipFile(package_path) as archive:
        answers = _read_jsonl(
            archive.read("answers.jsonl")
        )

        assert answers[0]["screenshot_path"] is None
        assert "screenshots/" in archive.namelist()


def test_export_deduplicates_tracking_url_sources(
        tmp_path: Path,
) -> None:
    task = GeoTask(
        task_id="Q004_expert",
        question_id="Q004",
        question="重复信源测试",
        mode=GeoMode.EXPERT,
    )

    source1 = GeoSource(
        occurrence_id="R1_S1",
        order=1,
        resolved_url="https://example.com/page?id=1",
    )

    source2 = GeoSource(
        occurrence_id="R1_S2",
        order=1,
        resolved_url=(
            "https://example.com/page"
            "?id=1&utm_source=test"
        ),
    )

    result = GeoRunResult(
        provider="deepseek",
        run_id="run_duplicate_source",
        task=task,
        answer_text_raw="正文-\n2\n。",
        answer_text_clean="正文。",
        sources=SourceCollection(
            status=SourceCollectionStatus.SUCCESS,
            declared_count=2,
            captured_count=2,
            unique_count=1,
            coverage_ratio=1.0,
            sources=[source1, source2],
        ),
        validation=ValidationResult(
            status=ValidationStatus.PASS,
        ),
        status=TaskStatus.SUCCESS,
    )

    package_path = export_geo_package(
        batch_id="batch_duplicate_source",
        results=[result],
        output_dir=tmp_path,
        product_id="hongmao_yaojiu",
        product_name="鸿茅药酒",
    )

    with zipfile.ZipFile(package_path) as archive:
        sources = _read_jsonl(
            archive.read("sources.jsonl")
        )

        assert len(sources) == 1
