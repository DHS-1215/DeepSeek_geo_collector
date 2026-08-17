import asyncio

from app.browser.session import BrowserSession
from app.core.config import load_settings


async def main() -> None:
    settings = load_settings()

    print(
        "Chrome",
        settings.chromium_executable_path,
    )

    async with BrowserSession(settings) as session:
        page = session.page
        await page.goto(
            settings.deepseek_url
        )

        print(
            "URL:",
            page.url,
        )

        print(
            "TITLE:",
            await page.title(),
        )

        input(
            "浏览器已打开，按 Enter 关闭..."
        )

if __name__ == "__main__":
    asyncio.run(main())
