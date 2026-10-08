import asyncio
import json
import zipfile
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

import app.pipeline.runner as pipeline_runner_module
from app.analysis.models import (
    ModelResponse,
)
from app.analysis.sentiment_config import (
    SentimentConfig,
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
    ValidationResult,
)
from app.pipeline.models import (
    PipelineStatus,
)


class NeutralProvider:
    provider_name = "integration-provider"
    model_name = "integration-model"

    async def health_check(
            self,
    ) -> bool:
        return True

    async def classify(
            self,
            *,
            system_prompt: str,
            user_prompt: str,
    ) -> ModelResponse:
        payload = {
            "target_name": (
                "\u9e3f\u8305\u836f\u9152"
            ),
            "sentiment": "neutral",
            "reason": "integration-test",
            "evidence": [],
            "confidence": 0.9,
        }

        return ModelResponse(
            payload=payload,
            latency_seconds=0.01,
            raw_content="integration-test",
            response_json_keys=list(
                payload.keys()
            ),
        )


def _read_jsonl(
        archive: zipfile.ZipFile,
        filename: str,
) -> list[dict]:
    text = (
        archive
        .read(filename)
        .decode("utf-8")
        .strip()
    )

    if not text:
        return []

    return [
        json.loads(line)
        for line in text.splitlines()
    ]


def test_pipeline_loads_csv_exports_and_verifies_package(
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
) -> None:
    csv_path = (
            tmp_path
            / "tasks.csv"
    )

    csv_path.write_text(
        (
            "question_id,question,mode\n"
            "Q001,鸿茅药酒是什么？,quick\n"
            "Q001,鸿茅药酒是什么？,expert\n"
        ),
        encoding="utf-8",
    )

    output_dir = (
            tmp_path
            / "package"
    )

    quick_result = GeoRunResult(
        provider="deepseek",
        run_id="run_quick_001",
        batch_id="batch_pipeline_001",
        task=GeoTask(
            task_id=(
                "batch_pipeline_001_"
                "Q001_quick"
            ),
            question_id="Q001",
            question="鸿茅药酒是什么？",
            mode=GeoMode.QUICK,
        ),
        answer_text_raw=(
            "鸿茅药酒是一种药品。"
        ),
        answer_text_clean=(
            "鸿茅药酒是一种药品。"
        ),
        sources=SourceCollection(
            status=(
                SourceCollectionStatus.SUCCESS
            ),
            declared_count=1,
            captured_count=1,
            unique_count=1,
            coverage_ratio=1.0,
            sources=[
                GeoSource(
                    occurrence_id="R1_S1",
                    order=1,
                    title="测试来源",
                    clean_title="测试来源",
                    site_name="example",
                    raw_href=(
                        "https://example.com/"
                        "article?id=1"
                    ),
                    resolved_url=(
                        "https://example.com/"
                        "article?id=1"
                    ),
                    domain="example.com",
                    source_round=1,
                )
            ],
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
        batch_id="batch_pipeline_001",
        task=GeoTask(
            task_id=(
                "batch_pipeline_001_"
                "Q001_expert"
            ),
            question_id="Q001",
            question="鸿茅药酒是什么？",
            mode=GeoMode.EXPERT,
        ),
        answer_text_raw=(
            "鸿茅药酒是一种药品。"
        ),
        answer_text_clean=(
            "鸿茅药酒是一种药品。"
        ),
        sources=SourceCollection(
            status=(
                SourceCollectionStatus
                .NOT_APPLICABLE
            ),
        ),
        validation=ValidationResult(
            status=ValidationStatus.PASS,
            is_complete=True,
        ),
        status=TaskStatus.SUCCESS,
    )

    batch_result = BatchResult(
        batch_id="batch_pipeline_001",
        status=BatchStatus.SUCCESS,
        results=[
            quick_result,
            expert_result,
        ],
        total_count=2,
        success_count=2,
        failed_count=0,
    )

    run_mock = AsyncMock(
        return_value=batch_result
    )

    monkeypatch.setattr(
        pipeline_runner_module,
        "run_batch",
        run_mock,
    )

    result = asyncio.run(
        pipeline_runner_module
        .run_collection_pipeline(
            csv_path=csv_path,
            batch_id="batch_pipeline_001",
            output_dir=output_dir,
            product_id="hongmao_yaojiu",
            product_name="鸿茅药酒",
            sentiment_provider=(
                NeutralProvider()
            ),
            sentiment_config=(
                SentimentConfig(
                    max_retries=0,
                )
            ),
        )
    )

    assert (
            result.status
            == PipelineStatus.PASS
    )

    assert (
            result.package_verified
            is True
    )

    assert (
            result.batch_result.total_count
            == 2
    )

    assert (
        result.package_path.exists()
    )

    passed_tasks = (
        run_mock.await_args.args[0]
    )

    assert len(passed_tasks) == 2

    assert (
            passed_tasks[0].task_id
            == (
                "batch_pipeline_001_"
                "Q001_quick"
            )
    )

    assert (
            passed_tasks[1].task_id
            == (
                "batch_pipeline_001_"
                "Q001_expert"
            )
    )

    with zipfile.ZipFile(
            result.package_path
    ) as archive:
        manifest = json.loads(
            archive.read(
                "manifest.json"
            )
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

        assert (
                manifest["batch_id"]
                == "batch_pipeline_001"
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

        assert len(tasks) == 2
        assert len(answers) == 2
        assert len(sources) == 1

        quick_answer = next(
            row
            for row in answers
            if row["mode_code"]
            == "quick"
        )

        expert_answer = next(
            row
            for row in answers
            if row["mode_code"]
            == "expert"
        )

        assert (
                quick_answer[
                    "source_collection_status"
                ]
                == "success"
        )

        assert (
                quick_answer[
                    "source_count_raw"
                ]
                == 1
        )

        assert (
                expert_answer[
                    "source_collection_status"
                ]
                == "not_supported"
        )

        assert (
                expert_answer[
                    "source_count_raw"
                ]
                == 0
        )
