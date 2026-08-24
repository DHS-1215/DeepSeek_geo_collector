import json
import zipfile
from pathlib import Path

from app.batch.export import (
    export_batch_package,
)
from app.batch.models import (
    BatchResult,
    BatchStatus,
)
from app.core.enums import (
    GeoMode,
    SourceCollectionStatus,
    TaskStatus,
    ValidationStatus,
)
from app.core.models import (
    GeoRunResult,
    GeoSource,
    GeoTask,
    SourceCollection,
    TimingInfo,
    ValidationResult,
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
        for line in text.splitlines()
    ]


def test_export_mixed_quick_and_expert_batch(
        tmp_path: Path,
) -> None:
    quick_task = GeoTask(
        task_id="batch_001_Q001_quick",
        question_id="Q001",
        question="鸿茅药酒是什么？",
        mode=GeoMode.QUICK,
    )

    expert_task = GeoTask(
        task_id="batch_001_Q001_expert",
        question_id="Q001",
        question="鸿茅药酒是什么？",
        mode=GeoMode.EXPERT,
    )

    quick_source = GeoSource(
        occurrence_id="R1_S1",
        order=1,
        title="测试来源",
        clean_title="测试来源",
        site_name="example",
        snippet="测试来源摘要",
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

    quick_result = GeoRunResult(
        provider="deepseek",
        run_id="run_quick_001",
        batch_id="batch_001",
        task=quick_task,
        answer_text_raw="Quick 原始回答",
        answer_text_clean="Quick 清洗回答",
        sources=SourceCollection(
            status=(
                SourceCollectionStatus.SUCCESS
            ),
            declared_count=1,
            captured_count=1,
            unique_count=1,
            coverage_ratio=1.0,
            sources=[
                quick_source,
            ],
        ),
        timing=TimingInfo(
            started_at=(
                "2026-08-24T10:00:00"
            ),
            finished_at=(
                "2026-08-24T10:00:05"
            ),
            elapsed_seconds=5.0,
        ),
        validation=ValidationResult(
            status=ValidationStatus.PASS,
            is_complete=True,
        ),
        status=TaskStatus.SUCCESS,
    )

    expert_result = GeoRunResult(
        provider="deepseek",
        run_id="run_expert_001",
        batch_id="batch_001",
        task=expert_task,
        answer_text_raw="Expert 原始回答",
        answer_text_clean="Expert 清洗回答",
        sources=SourceCollection(
            status=(
                SourceCollectionStatus.NOT_APPLICABLE
            ),
        ),
        timing=TimingInfo(
            started_at=(
                "2026-08-24T10:00:10"
            ),
            finished_at=(
                "2026-08-24T10:00:20"
            ),
            elapsed_seconds=10.0,
        ),
        validation=ValidationResult(
            status=ValidationStatus.PASS,
            is_complete=True,
        ),
        status=TaskStatus.SUCCESS,
    )

    batch_result = BatchResult(
        batch_id="batch_001",
        status=BatchStatus.SUCCESS,
        results=[
            quick_result,
            expert_result,
        ],
        total_count=2,
        success_count=2,
        failed_count=0,
    )

    package_path = export_batch_package(
        result=batch_result,
        output_dir=tmp_path,
        product_id="hongmao_yaojiu",
        product_name="鸿茅药酒",
    )

    assert package_path.exists()

    assert (
            package_path.name
            == "geo_package_deepseek_batch_001.zip"
    )

    with zipfile.ZipFile(
            package_path
    ) as archive:
        names = set(
            archive.namelist()
        )

        assert "manifest.json" in names
        assert "tasks.jsonl" in names
        assert "answers.jsonl" in names
        assert "sources.jsonl" in names
        assert "checksums.json" in names

        manifest = json.loads(
            archive.read(
                "manifest.json"
            )
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

        sources = _read_jsonl(
            archive.read(
                "sources.jsonl"
            )
        )

        assert (
                manifest["schema_version"]
                == "geo_package_v1"
        )

        assert (
                manifest["batch_id"]
                == "batch_001"
        )

        assert (
                manifest["task_count"]
                == 2
        )

        assert (
                manifest["answer_count"]
                == 2
        )

        assert (
                manifest["source_count"]
                == 1
        )

        assert (
                manifest["product_id"]
                == "hongmao_yaojiu"
        )

        assert (
                manifest["product_name"]
                == "鸿茅药酒"
        )

        assert len(tasks) == 2
        assert len(answers) == 2
        assert len(sources) == 1

        task_modes = {
            row["mode_code"]
            for row in tasks
        }

        assert task_modes == {
            "quick",
            "expert",
        }

        answers_by_mode = {
            row["mode_code"]: row
            for row in answers
        }

        assert (
                answers_by_mode[
                    "quick"
                ][
                    "source_collection_status"
                ]
                == "success"
        )

        assert (
                answers_by_mode[
                    "quick"
                ][
                    "source_count_raw"
                ]
                == 1
        )

        assert (
                answers_by_mode[
                    "expert"
                ][
                    "source_collection_status"
                ]
                == "not_supported"
        )

        assert (
                answers_by_mode[
                    "expert"
                ][
                    "source_count_raw"
                ]
                == 0
        )

        assert (
                sources[0]["mode_code"]
                == "quick"
        )

        assert (
                sources[0]["domain"]
                == "example.com"
        )

        assert (
                sources[0][
                    "normalized_source_url_raw"
                ]
                == (
                    "https://example.com/"
                    "page?id=1"
                )
        )
