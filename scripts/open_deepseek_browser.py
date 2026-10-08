import asyncio

from app.browser.session import BrowserSession
from app.core.config import load_settings


async def main() -> None:
    settings = load_settings()

    async with BrowserSession(settings) as session:
        page = session.page

        await page.goto(
            settings.deepseek_url,
            wait_until="domcontentloaded",
        )

        print("DeepSeek browser opened.")
        print("URL:", page.url)
        print()
        print(
            "You can now inspect/login manually."
        )
        print(
            "Press Ctrl+C here when finished."
        )

        while True:
            await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
