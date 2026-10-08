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
from app.pipeline.exceptions import (
    PipelinePausedError,
)

from app.analysis.models import (
    GeoAnalysisResult,
    MentionBatchResult,
    MentionSummary,
    SentimentBatchResult,
    SentimentSummary,
    SourceTop10Summary,
    TargetMentionSummary,
    TargetSentimentSummary,
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
        mention=MentionBatchResult(
            summaries={
                "product_001": (
                    TargetMentionSummary(
                        target_id=(
                            "product_001"
                        ),
                        target_name=(
                            "测试产品"
                        ),
                        quick=MentionSummary(
                            valid_count=2,
                            mentioned_count=1,
                            mention_rate=0.5,
                        ),
                        expert=MentionSummary(
                            valid_count=2,
                            mentioned_count=2,
                            mention_rate=1.0,
                        ),
                        all_answers=MentionSummary(
                            valid_count=4,
                            mentioned_count=3,
                            mention_rate=0.75,
                        ),
                        question_level=(
                            MentionSummary(
                                valid_count=2,
                                mentioned_count=2,
                                mention_rate=1.0,
                            )
                        ),
                    )
                )
            }
        ),

        sentiment=SentimentBatchResult(
            summaries={
                "product_001": (
                    TargetSentimentSummary(
                        target_id=(
                            "product_001"
                        ),
                        target_name=(
                            "测试产品"
                        ),
                        quick=SentimentSummary(
                            planned_mention_count=1,
                            classified_mention_count=1,
                            positive_count=0,
                            neutral_count=1,
                            negative_count=0,
                            non_negative_count=1,
                            non_negative_rate=1.0,
                        ),
                        expert=SentimentSummary(
                            planned_mention_count=2,
                            classified_mention_count=2,
                            positive_count=1,
                            neutral_count=0,
                            negative_count=1,
                            non_negative_count=1,
                            non_negative_rate=0.5,
                        ),
                        all_answers=SentimentSummary(
                            planned_mention_count=3,
                            classified_mention_count=3,
                            positive_count=1,
                            neutral_count=1,
                            negative_count=1,
                            non_negative_count=2,
                            non_negative_rate=(
                                    2 / 3
                            ),
                        ),
                        question_level=(
                            SentimentSummary(
                                planned_mention_count=2,
                                classified_mention_count=2,
                                positive_count=1,
                                neutral_count=0,
                                negative_count=1,
                                non_negative_count=1,
                                non_negative_rate=0.5,
                            )
                        ),
                    )
                )
            }
        ),

        sources=SourceTop10Summary(
            total_occurrences=10,
            top10_occurrences=8,
            top10_share=0.8,
            outside_top10_occurrences=2,
            outside_top10_share=0.2,
        ),

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


def test_cli_prints_geo_analysis_metrics(
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        cli_module,
        "run_collection_pipeline",
        AsyncMock(
            return_value=(
                _build_pipeline_result(
                    status=(
                        PipelineStatus.PASS
                    ),
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

    assert exit_code == 0

    output = (
        capsys
        .readouterr()
        .out
    )

    assert (
            "MENTION RATE (QUICK): 50.00%"
            in output
    )

    assert (
            "MENTION RATE (ALL): 75.00%"
            in output
    )

    assert (
            "NON-NEGATIVE RATE (QUICK): 100.00%"
            in output
    )

    assert (
            "NON-NEGATIVE RATE (ALL): 66.67%"
            in output
    )

    assert (
            "SOURCE TOP10 RATE: 80.00%"
            in output
    )

    assert (
            "SOURCE OCCURRENCES: 10"
            in output
    )



def test_cli_prints_na_when_sentiment_is_not_classified(
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
) -> None:
    pipeline_result = _build_pipeline_result(
        status=PipelineStatus.PASS,
    )

    sentiment_summary = (
        pipeline_result
        .analysis_result
        .sentiment
        .summaries[
            "product_001"
        ]
    )

    summaries = (
        sentiment_summary.quick,
        sentiment_summary.expert,
        sentiment_summary.all_answers,
        sentiment_summary.question_level,
    )

    for summary in summaries:
        summary.classified_mention_count = 0
        summary.non_negative_rate = 0.0

    monkeypatch.setattr(
        cli_module,
        "run_collection_pipeline",
        AsyncMock(
            return_value=pipeline_result
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
            "test-product",
        ]
    )

    assert exit_code == 0

    output = (
        capsys
        .readouterr()
        .out
    )

    assert (
        "NON-NEGATIVE RATE (QUICK): N/A"
        in output
    )

    assert (
        "NON-NEGATIVE RATE (EXPERT): N/A"
        in output
    )

    assert (
        "NON-NEGATIVE RATE (ALL): N/A"
        in output
    )

    assert (
        "NON-NEGATIVE RATE (QUESTION): N/A"
        in output
    )



def test_main_returns_four_for_pipeline_pause(
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        cli_module,
        "run_collection_pipeline",
        AsyncMock(
            side_effect=(
                PipelinePausedError(
                    batch_id=(
                        "batch_rate_limit_001"
                    ),
                    reason=(
                        "deepseek_rate_limit"
                    ),
                )
            )
        ),
    )

    exit_code = cli_module.main(
        [
            "--csv",
            "input/tasks.csv",
            "--batch-id",
            "batch_rate_limit_001",
            "--product-id",
            "hongmao_yaojiu",
            "--product-name",
            "test-product",
        ]
    )

    assert exit_code == 4

    output = (
        capsys
        .readouterr()
        .out
    )

    assert (
        "PIPELINE STATUS: PAUSED"
        in output
    )

    assert (
        "BATCH ID: batch_rate_limit_001"
        in output
    )

    assert (
        "REASON: deepseek_rate_limit"
        in output
    )

    assert (
        "CHECKPOINT: SAVED"
        in output
    )

    assert (
        "choose R to resume"
        in output
    )

    assert "Traceback" not in output



def test_main_returns_five_for_internal_error(
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        cli_module,
        "run_collection_pipeline",
        AsyncMock(
            side_effect=RuntimeError(
                "unexpected failure"
            )
        ),
    )

    exit_code = cli_module.main(
        [
            "--csv",
            "input/tasks.csv",
            "--batch-id",
            "batch_internal_error",
            "--product-id",
            "test_product",
            "--product-name",
            "test-product",
        ]
    )

    assert exit_code == 5

    output = (
        capsys
        .readouterr()
        .out
    )

    assert (
        "INTERNAL ERROR:"
        in output
    )

    assert (
        "unexpected failure"
        in output
    )
