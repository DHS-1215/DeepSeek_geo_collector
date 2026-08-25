from pathlib import Path
from unittest.mock import AsyncMock

import pytest

import app.pipeline.__main__ as cli_module
from app.batch.models import (
    BatchResult,
    BatchStatus,
)
from app.package.verifier import (
    PackageVerificationError,
)
from app.pipeline.models import (
    PipelineResult,
    PipelineStatus,
)

from app.analysis.models import (
    GeoAnalysisResult,
    MentionBatchResult,
    SentimentBatchResult,
    SourceTop10Summary,
)
from app.core.enums import GeoMode


def _build_pipeline_result(
        *,
        status: PipelineStatus,
        failed_count: int = 0,
) -> PipelineResult:
    total_count = 2

    success_count = (
            total_count
            -
            failed_count
    )

    batch_result = BatchResult(
        batch_id="batch_001",
        status=(
            BatchStatus.SUCCESS
            if failed_count == 0
            else BatchStatus.FAILED
        ),
        total_count=total_count,
        success_count=success_count,
        failed_count=failed_count,
    )

    analysis_result = GeoAnalysisResult(
        mention=MentionBatchResult(),
        sentiment=SentimentBatchResult(),
        sources=SourceTop10Summary(),
        source_mode=GeoMode.QUICK,
    )

    return PipelineResult(
        status=status,
        batch_result=batch_result,
        analysis_result=analysis_result,
        package_path=Path(
            "output/package/test.zip"
        ),
        package_verified=True,
    )


def test_parse_args() -> None:
    args = cli_module.parse_args(
        [
            "--csv",
            "input/tasks.csv",
            "--batch-id",
            "batch_001",
            "--product-id",
            "product_001",
            "--product-name",
            "测试产品",
        ]
    )

    assert (
            args.csv
            == Path("input/tasks.csv")
    )

    assert (
            args.batch_id
            == "batch_001"
    )

    assert (
            args.output_dir
            == Path("output/package")
    )

    assert (
            args.product_id
            == "product_001"
    )

    assert (
            args.product_name
            == "测试产品"
    )


def test_main_returns_zero_for_pass(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_mock = AsyncMock(
        return_value=(
            _build_pipeline_result(
                status=PipelineStatus.PASS,
            )
        )
    )

    monkeypatch.setattr(
        cli_module,
        "run_collection_pipeline",
        run_mock,
    )

    exit_code = cli_module.main(
        [
            "--csv",
            "input/tasks.csv",
            "--batch-id",
            "batch_001",
            "--product-id",
            "product_001",
            "--product-name",
            "测试产品",
        ]
    )

    assert exit_code == 0


def test_main_returns_one_for_task_failures(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_mock = AsyncMock(
        return_value=(
            _build_pipeline_result(
                status=(
                    PipelineStatus
                    .PASS_WITH_WARNINGS
                ),
                failed_count=1,
            )
        )
    )

    monkeypatch.setattr(
        cli_module,
        "run_collection_pipeline",
        run_mock,
    )

    exit_code = cli_module.main(
        [
            "--csv",
            "input/tasks.csv",
            "--batch-id",
            "batch_001",
            "--product-id",
            "product_001",
            "--product-name",
            "测试产品",
        ]
    )

    assert exit_code == 1


def test_main_returns_two_for_input_error(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        cli_module,
        "run_collection_pipeline",
        AsyncMock(
            side_effect=ValueError(
                "invalid batch"
            )
        ),
    )

    exit_code = cli_module.main(
        [
            "--csv",
            "input/tasks.csv",
            "--batch-id",
            "batch_001",
            "--product-id",
            "product_001",
            "--product-name",
            "测试产品",
        ]
    )

    assert exit_code == 2


def test_main_returns_three_for_package_verification_error(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        cli_module,
        "run_collection_pipeline",
        AsyncMock(
            side_effect=(
                PackageVerificationError(
                    "checksum mismatch"
                )
            )
        ),
    )

    exit_code = cli_module.main(
        [
            "--csv",
            "input/tasks.csv",
            "--batch-id",
            "batch_001",
            "--product-id",
            "product_001",
            "--product-name",
            "测试产品",
        ]
    )

    assert exit_code == 3
