import asyncio
from pathlib import Path
from unittest.mock import AsyncMock

from app.analysis.replay import (
    build_replay_results,
    replay_analysis,
)
from app.analysis.sentiment_config import (
    SentimentConfig,
)
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
from app.package.exporter import (
    export_geo_package,
)
from app.package.reader import (
    read_geo_package,
)


def _build_test_package(
        tmp_path: Path,
) -> Path:
    batch_id = "replay_test_batch"

    quick_result = GeoRunResult(
        provider="deepseek",
        run_id="run_quick_001",
        batch_id=batch_id,
        task=GeoTask(
            task_id=(
                f"{batch_id}_Q001_quick"
            ),
            question_id="Q001",
            question="test question",
            mode=GeoMode.QUICK,
        ),
        answer_text_raw=(
            "\\u9e3f\\u8305\\u836f\\u9152"
            " test answer"
        ),
        answer_text_clean=(
            "\\u9e3f\\u8305\\u836f\\u9152"
            " test answer"
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
        batch_id=batch_id,
        task=GeoTask(
            task_id=(
                f"{batch_id}_Q001_expert"
            ),
            question_id="Q001",
            question="test question",
            mode=GeoMode.EXPERT,
        ),
        answer_text_raw=(
            "\\u9e3f\\u8305\\u836f\\u9152"
            " expert answer"
        ),
        answer_text_clean=(
            "\\u9e3f\\u8305\\u836f\\u9152"
            " expert answer"
        ),
        validation=ValidationResult(
            status=ValidationStatus.PASS,
            is_complete=True,
        ),
        status=TaskStatus.SUCCESS,
    )

    return export_geo_package(
        batch_id=batch_id,
        results=[
            quick_result,
            expert_result,
        ],
        output_dir=tmp_path,
        product_id="hongmao_yaojiu",
        product_name=(
            "\\u9e3f\\u8305\\u836f\\u9152"
        ),
    )


def test_build_replay_results(
        tmp_path: Path,
) -> None:
    package_path = _build_test_package(
        tmp_path
    )

    package = read_geo_package(
        package_path
    )

    results = build_replay_results(
        package
    )

    assert len(results) == 2

    modes = {
        result.task.mode.value
        for result in results
    }

    assert modes == {
        "quick",
        "expert",
    }

    for result in results:
        assert (
            result.task.question_id
            == "Q001"
        )

        assert (
            result.answer_text_clean
            != ""
        )


def test_replay_analysis(
        monkeypatch,
        tmp_path: Path,
) -> None:
    package_path = _build_test_package(
        tmp_path
    )

    analysis_result = object()

    analysis_mock = AsyncMock(
        return_value=analysis_result
    )

    monkeypatch.setattr(
        "app.analysis.replay.run_geo_analysis",
        analysis_mock,
    )

    result = asyncio.run(
        replay_analysis(
            package_path=package_path,
            product_id="hongmao_yaojiu",
            product_name=(
                "\\u9e3f\\u8305\\u836f\\u9152"
            ),
            sentiment_provider=object(),
            sentiment_config=(
                SentimentConfig()
            ),
        )
    )

    assert result is analysis_result

    analysis_mock.assert_awaited_once()
