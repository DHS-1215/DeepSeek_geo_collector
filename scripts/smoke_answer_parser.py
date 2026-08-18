import argparse
import asyncio

from app.browser.session import BrowserSession
from app.core.config import load_settings
from app.deepseek.answer_parser import parse_answer
from app.deepseek.answer_waiter import wait_for_new_answer
from app.deepseek.page import DeepSeekPage


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
        await deepseek.set_quick_mode()

        previous_count = (
            await deepseek
            .assistant_messages()
            .count()
        )

        await deepseek.fill_question(
            args.question
        )

        await deepseek.submit_question()

        await wait_for_new_answer(
            page,
            previous_answer_count=previous_count,
            timeout_seconds=(
                settings.quick_max_wait_seconds
            ),
        )

        answer = (
            deepseek
            .assistant_messages()
            .last
        )

        result = await parse_answer(
            answer
        )

        print()
        print("CITATION COUNT:",
              result.citation_count)

        print()
        print("=" * 80)
        print("RAW")
        print("=" * 80)
        print(result.raw_text)

        print()
        print("=" * 80)
        print("CLEAN")
        print("=" * 80)
        print(result.clean_text)

        input(
            "验证完成，按 Enter 关闭..."
        )


if __name__ == "__main__":
    asyncio.run(main())
