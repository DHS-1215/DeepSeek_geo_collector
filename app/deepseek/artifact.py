from pathlib import Path

from playwright.async_api import Page

from app.core.models import ArtifactInfo


async def capture_artifacts(
        page: Page,
        run_id: str,
        output_dir: Path,
) -> ArtifactInfo:
    """
    保存 DeepSeek 页面采集证据。
    """

    artifact_dir = (
            output_dir
            / "artifacts"
            / run_id
    )

    print(
        "ARTIFACT DIR:",
        artifact_dir
    )

    artifact_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    screenshot_path = (
            artifact_dir
            / "page.png"
    )

    html_path = (
            artifact_dir
            / "page.html"
    )

    await page.screenshot(
        path=str(screenshot_path),
        full_page=True,
    )

    html = await page.content()

    html_path.write_text(
        html,
        encoding="utf-8",
    )

    return ArtifactInfo(
        screenshot_path=str(
            screenshot_path
        ),
        raw_html_path=str(
            html_path
        ),
    )
