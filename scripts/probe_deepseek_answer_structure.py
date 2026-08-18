import argparse
import asyncio
import json

from app.browser.session import BrowserSession
from app.core.config import load_settings
from app.deepseek.answer_waiter import wait_for_new_answer
from app.deepseek.page import DeepSeekPage
from app.deepseek.selectors import ASSISTANT_MESSAGE_MAIN


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--question",
        required=True,
    )

    return parser.parse_args()


async def main() -> None:
    args = parse_args()
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

        previous_answer_count = (
            await deepseek.assistant_messages().count()
        )

        await deepseek.fill_question(
            args.question
        )

        await deepseek.submit_question()

        result = await wait_for_new_answer(
            page,
            previous_answer_count=previous_answer_count,
            timeout_seconds=settings.quick_max_wait_seconds,
        )

        answer = page.locator(
            ASSISTANT_MESSAGE_MAIN
        ).last

        print()
        print("=" * 80)
        print("RAW INNER TEXT")
        print("=" * 80)
        print(result.text)

        structure = await answer.evaluate(
            """
            el => ({
                inner_html: el.innerHTML,
                links: [...el.querySelectorAll("a")].map((node, index) => ({
                    index,
                    text: (node.innerText || node.textContent || "").trim(),
                    href: node.getAttribute("href"),
                    class_name: node.className?.toString() || "",
                    outer_html: node.outerHTML.slice(0, 1000)
                })),
                superscripts: [...el.querySelectorAll("sup")].map((node, index) => ({
                    index,
                    text: (node.innerText || node.textContent || "").trim(),
                    class_name: node.className?.toString() || "",
                    outer_html: node.outerHTML.slice(0, 1000)
                })),
                spans: [...el.querySelectorAll("span")].map((node, index) => ({
                    index,
                    text: (node.innerText || node.textContent || "").trim(),
                    class_name: node.className?.toString() || "",
                    outer_html: node.outerHTML.slice(0, 600)
                }))
            })
            """
        )

        print()
        print("=" * 80)
        print("LINKS")
        print("=" * 80)

        for item in structure["links"]:
            print(
                json.dumps(
                    item,
                    ensure_ascii=False,
                )
            )

        print()
        print("=" * 80)
        print("SUPERSCRIPTS")
        print("=" * 80)

        for item in structure["superscripts"]:
            print(
                json.dumps(
                    item,
                    ensure_ascii=False,
                )
            )

        print()
        print("=" * 80)
        print("SPANS")
        print("=" * 80)

        for item in structure["spans"]:
            if item["text"]:
                print(
                    json.dumps(
                        item,
                        ensure_ascii=False,
                    )
                )

        print()
        print("=" * 80)
        print("INNER HTML")
        print("=" * 80)
        print(
            structure["inner_html"]
        )

        input(
            "探针完成，按 Enter 关闭..."
        )


if __name__ == "__main__":
    asyncio.run(main())
