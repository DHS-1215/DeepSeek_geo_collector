from datetime import datetime
from uuid import uuid4

from app.browser.session import BrowserSession
from app.core.config import load_settings
from app.core.enums import (
    GeoMode,
    TaskStatus,
)
from app.core.models import (
    ArtifactInfo,
    FailureInfo,
    GeoRunResult,
    GeoTask,
    TimingInfo,
)
from app.deepseek.answer_parser import parse_answer
from app.deepseek.answer_waiter import (
    wait_for_new_answer,
)
from app.deepseek.artifact import (
    capture_artifacts,
)
from app.deepseek.error_classifier import (
    classify_failure,
    is_retryable_failure,
)
from app.deepseek.page import DeepSeekPage
from app.deepseek.source_collector import (
    collect_sources,
)


async def run_deepseek_task(
        task: GeoTask,
        batch_id: str | None = None,
) -> GeoRunResult:
    """
    执行单个 DeepSeek GEO 采集任务。
    """

    settings = load_settings()

    run_id = (
        f"run_{uuid4().hex[:12]}"
    )

    started_at = datetime.now().isoformat()

    page = None

    try:
        async with BrowserSession(
                settings
        ) as session:

            page = session.page

            await page.goto(
                settings.deepseek_url,
                wait_until="domcontentloaded",
            )

            deepseek = DeepSeekPage(page)

            await deepseek.ensure_ready()

            if task.mode == GeoMode.QUICK:
                await deepseek.set_quick_mode()

            elif task.mode == GeoMode.EXPERT:
                await deepseek.set_expert_mode()

            previous_count = (
                await deepseek
                .assistant_messages()
                .count()
            )

            await deepseek.fill_question(
                task.question
            )

            await deepseek.submit_question()

            result = await wait_for_new_answer(
                page,
                previous_answer_count=previous_count,
                timeout_seconds=(
                    settings.quick_max_wait_seconds
                    if task.mode == GeoMode.QUICK
                    else settings.expert_max_wait_seconds
                ),
                stable_seconds=10.0,
            )

            answer_locator = (
                deepseek
                .assistant_messages()
                .last
            )

            parsed = await parse_answer(
                answer_locator
            )

            sources = await collect_sources(
                deepseek
            )

            artifacts = await capture_artifacts(
                page,
                run_id,
                settings.output_dir,
            )

            finished_at = (
                datetime.now().isoformat()
            )

            return GeoRunResult(
                provider="deepseek",
                run_id=run_id,
                task=task,
                batch_id=batch_id,

                answer_text_raw=(
                    parsed.raw_text
                ),

                answer_text_clean=(
                    parsed.clean_text
                ),

                sources=sources,

                artifacts=artifacts,

                timing=TimingInfo(
                    started_at=started_at,
                    finished_at=finished_at,
                    elapsed_seconds=(
                        result.elapsed_seconds
                    ),
                ),

                status=TaskStatus.SUCCESS,
            )

    except Exception as exc:

        artifacts = ArtifactInfo()

        if page is not None:
            artifacts = await capture_artifacts(
                page,
                run_id,
                settings.output_dir,
            )

        failure_type = classify_failure(
            exc
        )

        retryable = is_retryable_failure(
            failure_type
        )

        return GeoRunResult(
            provider="deepseek",
            run_id=run_id,
            task=task,
            batch_id=batch_id,

            artifacts=artifacts,

            failure=FailureInfo(
                type=failure_type,
                message=str(exc),
                retryable=retryable,
            ),

            status=TaskStatus.FAILED,
        )
