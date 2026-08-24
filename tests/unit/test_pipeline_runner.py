import asyncio
from pathlib import Path
from unittest.mock import (
    AsyncMock,
    Mock,
)

import pytest

import app.pipeline.runner as pipeline_runner_module
from app.batch.models import (
    BatchResult,
    BatchStatus,
)
from app.pipeline.models import (
    PipelineStatus,
)


def test_run_collection_pipeline_success(
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
) -> None:
    tasks = [
        object(),
        object(),
    ]

    batch_result = BatchResult(
        batch_id="batch_001",
        status=BatchStatus.SUCCESS,
        total_count=2,
        success_count=2,
        failed_count=0,
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
        "export_batch_package",
        export_mock,
    )

    monkeypatch.setattr(
        pipeline_runner_module,
        "verify_geo_package",
        verify_mock,
    )

    result = asyncio.run(
        pipeline_runner_module
        .run_collection_pipeline(
            csv_path=Path(
                "input/tasks.csv"
            ),
            batch_id="batch_001",
            output_dir=tmp_path,
            product_id="product_001",
            product_name="测试产品",
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
            product_id="product_001",
            product_name="测试产品",
        )
    )

    assert (
            result.status
            == PipelineStatus.PASS_WITH_WARNINGS
    )

    assert (
            result.batch_result.failed_count
            == 1
    )


def test_run_collection_pipeline_rejects_empty_batch(
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
) -> None:
    run_mock = AsyncMock()

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
                product_id="product_001",
                product_name="测试产品",
            )
        )

    run_mock.assert_not_awaited()
