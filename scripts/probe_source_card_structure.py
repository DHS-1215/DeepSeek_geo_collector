import asyncio
import json

from app.browser.session import BrowserSession
from app.core.config import load_settings
from app.deepseek.page import DeepSeekPage
from app.deepseek.answer_waiter import (
    wait_for_new_answer,
)


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

        count = (
            await deepseek
            .assistant_messages()
            .count()
        )

        await deepseek.fill_question(
            "鸿茅药酒是正规药品吗？需要医生处方吗？"
        )

        await deepseek.submit_question()

        await wait_for_new_answer(
            page,
            previous_answer_count=count,
            timeout_seconds=180,
            stable_seconds=5,
        )

        # 展开来源
        indicator = (
            deepseek
            .read_webpages_indicator()
            .last
        )

        await indicator.click()

        await page.wait_for_timeout(
            1000
        )

        card = (
            deepseek
            .source_cards()
            .first
        )

        result = await card.evaluate(
            """
            el => ({
                text: el.innerText,

                children:
                    [...el.querySelectorAll("*")]
                    .map(node => ({
                        tag: node.tagName,
                        text:
                            (
                              node.innerText
                              || ""
                            ).trim(),

                        class:
                            node.className
                            ?.toString()
                            || "",

                        title:
                            node.getAttribute(
                                "title"
                            ),

                        aria:
                            node.getAttribute(
                                "aria-label"
                            )
                    }))
                    .slice(0,50)
            })
            """
        )

        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
            )
        )

        input("结束")


if __name__ == "__main__":
    asyncio.run(main())
