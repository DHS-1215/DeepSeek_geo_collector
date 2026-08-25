from pathlib import Path

from app.analysis.replay import (
    build_replay_results,
)
from app.analysis.sentiment_config import SentimentConfig
from app.package.reader import (
    read_geo_package,
)
import asyncio
from unittest.mock import AsyncMock

from app.analysis.replay import (
    replay_analysis,
)


def test_build_replay_results() -> None:
    package = read_geo_package(
        Path(
            "output/w12_metrics/"
            "geo_package_deepseek_w12_metrics_smoke.zip"
        )
    )

    results = build_replay_results(
        package
    )

    assert len(results) == 16

    first = results[0]

    assert (
            first.task.question_id
            != ""
    )

    assert (
            first.answer_text_clean
            != ""
    )

    assert (
            first.task.mode.value
            in {
                "quick",
                "expert",
            }
    )


def test_replay_analysis(
        monkeypatch,
) -> None:
    analysis_result = object()

    monkeypatch.setattr(
        "app.analysis.replay.run_geo_analysis",
        AsyncMock(
            return_value=analysis_result
        ),
    )

    result = asyncio.run(
        replay_analysis(
            package_path=Path(
                "output/w12_metrics/"
                "geo_package_deepseek_w12_metrics_smoke.zip"
            ),
            product_id="hongmao_yaojiu",
            product_name="鸿茅药酒",
            sentiment_provider=object(),
            sentiment_config=SentimentConfig(),
        )
    )

    assert result is analysis_result
