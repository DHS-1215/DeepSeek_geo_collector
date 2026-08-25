import asyncio
from pathlib import Path
from unittest.mock import (
    AsyncMock,
    Mock,
)

from app.core.enums import (
    GeoMode,
    TaskStatus,
)

from app.core.models import (
    GeoRunResult,
    GeoTask,
)

import pytest

import app.pipeline.runner as pipeline_runner_module

from app.analysis.models import (
    GeoAnalysisResult,
    MentionBatchResult,
    MentionTarget,
    SentimentBatchResult,
    SourceTop10Summary,
    SentimentResult,
    SentimentStatus,
)
from app.analysis.sentiment_config import (
    SentimentConfig,
)
from app.batch.models import (
    BatchResult,
    BatchStatus,
)

from app.pipeline.models import (
    PipelineStatus,
)


def _analysis_result() -> GeoAnalysisResult:
    return GeoAnalysisResult(
        mention=MentionBatchResult(),
        sentiment=SentimentBatchResult(),
        sources=SourceTop10Summary(),
        source_mode=GeoMode.QUICK,
    )


def test_build_analysis_targets() -> None:
    targets = (
        pipeline_runner_module
        .build_analysis_targets(
            product_id="hongmao_yaojiu",
            product_name="鸿茅药酒",
        )
    )

    assert len(targets) == 1

    target = targets[0]

    assert (
            target.target_id
            == "hongmao_yaojiu"
    )

    assert (
            target.name
            == "鸿茅药酒"
    )

    assert target.aliases == [
        "鸿茅药酒"
    ]


def test_run_collection_pipeline_success(
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
) -> None:
    tasks = [
        object(),
        object(),
    ]

    task = GeoTask(
        task_id="Q001_quick",
        question_id="Q001",
        question="测试问题",
        mode=GeoMode.QUICK,
    )

    batch_result = BatchResult(
        batch_id="batch_003",
        status=BatchStatus.SUCCESS,
        total_count=1,
        success_count=1,
        failed_count=0,
        results=[
            GeoRunResult(
                provider="test",
                run_id="run_001",
                task=task,
                batch_id="batch_003",
                status=TaskStatus.SUCCESS,
            )
        ],
    )

    analysis_result = (
        _analysis_result()
    )

    package_path = (
            tmp_path
            / "geo_package_deepseek_batch_001.zip"
    )

    load_mock = Mock(
        return_value=tasks
    )

    run_mock = AsyncMock(
        return_value=batch_result
    )

    analysis_mock = AsyncMock(
        return_value=analysis_result
    )

    export_mock = Mock(
        return_value=package_path
    )

    verify_mock = Mock()

    monkeypatch.setattr(
        pipeline_runner_module,
        "load_batch_tasks",
        load_mock,
    )

    monkeypatch.setattr(
        pipeline_runner_module,
        "run_batch",
        run_mock,
    )

    monkeypatch.setattr(
        pipeline_runner_module,
        "run_geo_analysis",
        analysis_mock,
    )

    monkeypatch.setattr(
        pipeline_runner_module,
        "export_batch_package",
        export_mock,
    )

    monkeypatch.setattr(
        pipeline_runner_module,
        "verify_geo_package",
        verify_mock,
    )

    sentiment_provider = object()

    sentiment_config = (
        SentimentConfig()
    )

    result = asyncio.run(
        pipeline_runner_module
        .run_collection_pipeline(
            csv_path=Path(
                "input/tasks.csv"
            ),
            batch_id="batch_001",
            output_dir=tmp_path,
            product_id=(
                "hongmao_yaojiu"
            ),
            product_name="鸿茅药酒",
            sentiment_provider=(
                sentiment_provider
            ),
            sentiment_config=(
                sentiment_config
            ),
        )
    )

    assert (
            result.status
            == PipelineStatus.PASS
    )

    assert (
            result.batch_result
            is batch_result
    )

    assert (
            result.analysis_result
            is analysis_result
    )

    assert (
            result.package_path
            == package_path
    )

    assert (
            result.package_verified
            is True
    )

    run_mock.assert_awaited_once_with(
        tasks
    )

    analysis_mock.assert_awaited_once_with(
        results=batch_result.results,
        targets=[
            MentionTarget(
                target_id=(
                    "hongmao_yaojiu"
                ),
                name="鸿茅药酒",
                aliases=[
                    "鸿茅药酒"
                ],
            )
        ],
        sentiment_provider=(
            sentiment_provider
        ),
        sentiment_config=(
            sentiment_config
        ),
        source_mode=GeoMode.QUICK,
    )

    export_mock.assert_called_once_with(
        result=batch_result,
        output_dir=tmp_path,
        product_id=(
            "hongmao_yaojiu"
        ),
        product_name="鸿茅药酒",
    )

    verify_mock.assert_called_once_with(
        package_path
    )


def test_run_collection_pipeline_returns_warning_status(
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
) -> None:
    tasks = [
        object(),
        object(),
    ]

    batch_result = BatchResult(
        batch_id="batch_002",
        status=BatchStatus.FAILED,
        total_count=2,
        success_count=1,
        failed_count=1,
    )

    package_path = (
            tmp_path
            / "geo_package_deepseek_batch_002.zip"
    )

    monkeypatch.setattr(
        pipeline_runner_module,
        "load_batch_tasks",
        Mock(
            return_value=tasks
        ),
    )

    monkeypatch.setattr(
        pipeline_runner_module,
        "run_batch",
        AsyncMock(
            return_value=batch_result
        ),
    )

    monkeypatch.setattr(
        pipeline_runner_module,
        "run_geo_analysis",
        AsyncMock(
            return_value=(
                _analysis_result()
            )
        ),
    )

    monkeypatch.setattr(
        pipeline_runner_module,
        "export_batch_package",
        Mock(
            return_value=package_path
        ),
    )

    monkeypatch.setattr(
        pipeline_runner_module,
        "verify_geo_package",
        Mock(),
    )

    result = asyncio.run(
        pipeline_runner_module
        .run_collection_pipeline(
            csv_path=Path(
                "input/tasks.csv"
            ),
            batch_id="batch_002",
            output_dir=tmp_path,
            product_id=(
                "hongmao_yaojiu"
            ),
            product_name="鸿茅药酒",
            sentiment_provider=object(),
            sentiment_config=(
                SentimentConfig()
            ),
        )
    )

    assert (
            result.status
            == PipelineStatus
            .PASS_WITH_WARNINGS
    )

    assert (
            result.batch_result
            .failed_count
            == 1
    )


def test_run_collection_pipeline_rejects_empty_batch(
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
) -> None:
    run_mock = AsyncMock()

    analysis_mock = AsyncMock()

    monkeypatch.setattr(
        pipeline_runner_module,
        "load_batch_tasks",
        Mock(
            return_value=[]
        ),
    )

    monkeypatch.setattr(
        pipeline_runner_module,
        "run_batch",
        run_mock,
    )

    monkeypatch.setattr(
        pipeline_runner_module,
        "run_geo_analysis",
        analysis_mock,
    )

    with pytest.raises(
            ValueError,
            match="contains no tasks",
    ):
        asyncio.run(
            pipeline_runner_module
            .run_collection_pipeline(
                csv_path=Path(
                    "input/empty.csv"
                ),
                batch_id="batch_empty",
                output_dir=tmp_path,
                product_id=(
                    "hongmao_yaojiu"
                ),
                product_name="鸿茅药酒",
            )
        )

    run_mock.assert_not_awaited()

    analysis_mock.assert_not_awaited()


@pytest.mark.parametrize(
    (
            "product_id",
            "product_name",
            "error_message",
    ),
    [
        (
                "",
                "鸿茅药酒",
                "product_id cannot be empty",
        ),
        (
                "hongmao_yaojiu",
                "",
                "product_name cannot be empty",
        ),
    ],
)
def test_build_analysis_targets_rejects_empty_values(
        product_id: str,
        product_name: str,
        error_message: str,
) -> None:
    with pytest.raises(
            ValueError,
            match=error_message,
    ):
        (
            pipeline_runner_module
            .build_analysis_targets(
                product_id=product_id,
                product_name=product_name,
            )
        )


def test_pipeline_warns_when_sentiment_analysis_fails(
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
) -> None:
    tasks = [
        object()
    ]

    task = GeoTask(
        task_id="Q001_quick",
        question_id="Q001",
        question="测试问题",
        mode=GeoMode.QUICK,
    )

    batch_result = BatchResult(
        batch_id="batch_003",
        status=BatchStatus.SUCCESS,
        total_count=1,
        success_count=1,
        failed_count=0,
        results=[
            GeoRunResult(
                provider="test",
                run_id="run_001",
                task=task,
                batch_id="batch_003",
                status=TaskStatus.SUCCESS,
            )
        ],
    )

    analysis_result = GeoAnalysisResult(
        mention=MentionBatchResult(),

        sentiment=SentimentBatchResult(
            details={
                "Q001_quick": {
                    "hongmao_yaojiu": (
                        SentimentResult(
                            target_id=(
                                "hongmao_yaojiu"
                            ),
                            status=(
                                SentimentStatus
                                .TIMEOUT
                            ),
                            error_type=(
                                "timeout"
                            ),
                        )
                    )
                }
            }
        ),

        sources=SourceTop10Summary(),

        source_mode=GeoMode.QUICK,
    )

    package_path = (
            tmp_path
            / "geo_package.zip"
    )

    monkeypatch.setattr(
        pipeline_runner_module,
        "load_batch_tasks",
        Mock(
            return_value=tasks
        ),
    )

    monkeypatch.setattr(
        pipeline_runner_module,
        "run_batch",
        AsyncMock(
            return_value=batch_result
        ),
    )

    monkeypatch.setattr(
        pipeline_runner_module,
        "run_geo_analysis",
        AsyncMock(
            return_value=(
                analysis_result
            )
        ),
    )

    monkeypatch.setattr(
        pipeline_runner_module,
        "export_batch_package",
        Mock(
            return_value=(
                package_path
            )
        ),
    )

    monkeypatch.setattr(
        pipeline_runner_module,
        "verify_geo_package",
        Mock(),
    )

    result = asyncio.run(
        pipeline_runner_module
        .run_collection_pipeline(
            csv_path=Path(
                "input/tasks.csv"
            ),
            batch_id="batch_003",
            output_dir=tmp_path,
            product_id=(
                "hongmao_yaojiu"
            ),
            product_name="鸿茅药酒",
            sentiment_provider=object(),
            sentiment_config=(
                SentimentConfig()
            ),
        )
    )

    assert (
            batch_result.failed_count
            == 0
    )

    assert (
            result.status
            == PipelineStatus
            .PASS_WITH_WARNINGS
    )
