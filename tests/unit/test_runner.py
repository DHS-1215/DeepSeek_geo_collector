import asyncio
from pathlib import Path
from unittest.mock import (
    AsyncMock,
    MagicMock,
)

from app.core.enums import (
    FailureType,
    GeoMode,
    TaskStatus,
)
from app.core.models import (
    ArtifactInfo,
    GeoTask,
)
from app.deepseek.runner import (
    run_deepseek_task,
)


def test_runner_captures_artifact_when_page_failure(
        monkeypatch,
) -> None:
    import app.deepseek.runner as runner

    settings = MagicMock()
    settings.deepseek_url = (
        "https://chat.deepseek.com"
    )
    settings.output_dir = Path(
        "output"
    )

    monkeypatch.setattr(
        runner,
        "load_settings",
        MagicMock(
            return_value=settings
        ),
    )

    page = MagicMock()
    page.goto = AsyncMock()

    session = MagicMock()
    session.page = page

    browser_session = MagicMock()
    browser_session.__aenter__ = AsyncMock(
        return_value=session
    )
    browser_session.__aexit__ = AsyncMock(
        return_value=None
    )

    monkeypatch.setattr(
        runner,
        "BrowserSession",
        MagicMock(
            return_value=browser_session
        ),
    )

    deepseek = MagicMock()

    deepseek.ensure_ready = AsyncMock(
        side_effect=RuntimeError(
            "forced failure"
        )
    )

    monkeypatch.setattr(
        runner,
        "DeepSeekPage",
        MagicMock(
            return_value=deepseek
        ),
    )

    artifacts = ArtifactInfo(
        screenshot_path=(
            "output/artifacts/test/page.png"
        ),
        raw_html_path=(
            "output/artifacts/test/page.html"
        ),
    )

    capture_artifacts = AsyncMock(
        return_value=artifacts
    )

    monkeypatch.setattr(
        runner,
        "capture_artifacts",
        capture_artifacts,
    )

    task = GeoTask(
        task_id="test_task",
        question_id="Q001",
        question="测试问题",
        mode=GeoMode.QUICK,
    )

    result = asyncio.run(
        run_deepseek_task(task)
    )

    assert (
            result.status
            == TaskStatus.FAILED
    )

    assert result.failure is not None

    assert (
            result.failure.type
            == FailureType.ACQUISITION_FAILED
    )

    assert (
            result.failure.message
            == "forced failure"
    )

    assert (
            result.artifacts.screenshot_path
            == "output/artifacts/test/page.png"
    )

    assert (
            result.artifacts.raw_html_path
            == "output/artifacts/test/page.html"
    )

    capture_artifacts.assert_awaited_once()

    call_args = (
        capture_artifacts.await_args.args
    )

    assert call_args[0] is page
    assert call_args[2] == Path("output")


def test_runner_skips_artifact_when_browser_fails(
        monkeypatch,
) -> None:
    import app.deepseek.runner as runner

    settings = MagicMock()
    settings.output_dir = Path(
        "output"
    )

    monkeypatch.setattr(
        runner,
        "load_settings",
        MagicMock(
            return_value=settings
        ),
    )

    browser_session = MagicMock()

    browser_session.__aenter__ = AsyncMock(
        side_effect=RuntimeError(
            "browser failed"
        )
    )

    browser_session.__aexit__ = AsyncMock(
        return_value=None
    )

    monkeypatch.setattr(
        runner,
        "BrowserSession",
        MagicMock(
            return_value=browser_session
        ),
    )

    capture_artifacts = AsyncMock()

    monkeypatch.setattr(
        runner,
        "capture_artifacts",
        capture_artifacts,
    )

    task = GeoTask(
        task_id="test_task",
        question_id="Q001",
        question="测试问题",
        mode=GeoMode.QUICK,
    )

    result = asyncio.run(
        run_deepseek_task(task)
    )

    assert (
            result.status
            == TaskStatus.FAILED
    )

    assert result.failure is not None

    assert (
            result.failure.type
            == FailureType.ACQUISITION_FAILED
    )

    assert (
            result.failure.message
            == "browser failed"
    )

    capture_artifacts.assert_not_awaited()

    assert (
            result.artifacts.screenshot_path
            is None
    )

    assert (
            result.artifacts.raw_html_path
            is None
    )
