import asyncio
import json

from app.browser.session import BrowserSession
from app.core.config import load_settings
from app.deepseek.page import DeepSeekPage


async def main():
    settings = load_settings()

    async with BrowserSession(settings) as session:
        page = session.page

        await page.goto(
            settings.deepseek_url,
            wait_until="domcontentloaded",
        )

        deepseek = DeepSeekPage(page)

        await deepseek.ensure_ready()
        await deepseek.set_quick_mode()

        await page.wait_for_timeout(
            3000
        )

        cards = deepseek.source_cards()

        print(
            "CARD COUNT:",
            await cards.count()
        )

        first = cards.first

        result = await first.evaluate(
            """
            el => {
                return {
                    text: el.innerText,
                    html: el.outerHTML.slice(
                        0,
                        3000
                    )
                }
            }
            """
        )

        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
            )
        )

        input(
            "完成"
        )


if __name__ == "__main__":
    asyncio.run(main())
