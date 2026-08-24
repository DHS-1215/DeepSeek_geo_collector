import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import (
    AsyncMock,
    MagicMock,
)
from app.core.enums import (
    FailureType,
    GeoMode,
    SourceCollectionStatus,
    TaskStatus,
    ValidationStatus,
)
from app.core.models import (
    ArtifactInfo,
    GeoTask,
    SourceCollection,
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

    assert result.validation is not None

    assert (
            result.validation.status
            == ValidationStatus.FAIL
    )

    assert (
            result.validation.is_complete
            is False
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
            result.failure.retryable
            is False
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

    assert result.validation is not None

    assert (
            result.validation.status
            == ValidationStatus.FAIL
    )

    assert (
            result.validation.is_complete
            is False
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

    assert (
            result.failure.retryable
            is False
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


def test_runner_marks_timeout_as_retryable(
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
        side_effect=TimeoutError(
            "answer timed out"
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
            "output/artifacts/timeout/page.png"
        ),
        raw_html_path=(
            "output/artifacts/timeout/page.html"
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
        task_id="test_timeout",
        question_id="Q002",
        question="超时测试问题",
        mode=GeoMode.QUICK,
    )

    result = asyncio.run(
        run_deepseek_task(task)
    )

    assert (
            result.status
            == TaskStatus.FAILED
    )

    assert (
            result.status
            == TaskStatus.FAILED
    )

    assert result.validation is not None

    assert (
            result.validation.status
            == ValidationStatus.FAIL
    )

    assert (
            result.validation.is_complete
            is False
    )

    assert result.failure is not None

    assert (
            result.failure.type
            == FailureType.ANSWER_TIMEOUT
    )

    assert (
            result.failure.message
            == "answer timed out"
    )

    assert (
            result.failure.retryable
            is True
    )

    capture_artifacts.assert_awaited_once()


def test_runner_validates_successful_result(
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

    settings.quick_max_wait_seconds = 180

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

    messages = MagicMock()

    messages.count = AsyncMock(
        return_value=0
    )

    answer_locator = MagicMock()
    messages.last = answer_locator

    deepseek = MagicMock()

    deepseek.ensure_ready = AsyncMock()

    deepseek.set_quick_mode = AsyncMock()

    deepseek.assistant_messages = MagicMock(
        return_value=messages
    )

    deepseek.fill_question = AsyncMock()

    deepseek.submit_question = AsyncMock()

    monkeypatch.setattr(
        runner,
        "DeepSeekPage",
        MagicMock(
            return_value=deepseek
        ),
    )

    monkeypatch.setattr(
        runner,
        "wait_for_new_answer",
        AsyncMock(
            return_value=SimpleNamespace(
                elapsed_seconds=1.5,
            )
        ),
    )

    monkeypatch.setattr(
        runner,
        "parse_answer",
        AsyncMock(
            return_value=SimpleNamespace(
                raw_text="测试回答",
                clean_text="测试回答",
            )
        ),
    )

    monkeypatch.setattr(
        runner,
        "collect_sources",
        AsyncMock(
            return_value=SourceCollection(
                status=(
                    SourceCollectionStatus.SUCCESS
                ),
            )
        ),
    )

    monkeypatch.setattr(
        runner,
        "capture_artifacts",
        AsyncMock(
            return_value=ArtifactInfo()
        ),
    )

    task = GeoTask(
        task_id="test_success",
        question_id="Q003",
        question="测试成功问题",
        mode=GeoMode.QUICK,
    )

    result = asyncio.run(
        run_deepseek_task(task)
    )

    assert (
            result.status
            == TaskStatus.SUCCESS
    )

    assert (
            result.answer_text_clean
            == "测试回答"
    )

    assert result.validation is not None

    assert (
            result.validation.status
            == ValidationStatus.PASS
    )

    assert (
            result.validation.is_complete
            is True
    )

    assert result.failure is None
