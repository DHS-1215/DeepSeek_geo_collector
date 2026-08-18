import argparse
import asyncio
from datetime import datetime

from app.deepseek.answer_parser import parse_answer
from app.browser.session import BrowserSession
from app.core.config import load_settings
from app.deepseek.answer_waiter import (
    wait_for_new_answer,
)
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

        previous_answer_count = (
            await deepseek
            .assistant_messages()
            .count()
        )

        print(
            "ASSISTANT COUNT BEFORE:",
            previous_answer_count,
        )

        await deepseek.fill_question(
            args.question
        )

        await deepseek.submit_question()

        print(
            "QUESTION SENT:",
            args.question,
        )

        result = await wait_for_new_answer(
            page,
            previous_answer_count=(
                previous_answer_count
            ),
            timeout_seconds=(
                settings.quick_max_wait_seconds
            ),

            stable_seconds=5.0,
        )
        answer = (
            deepseek
            .assistant_messages()
            .last
        )

        parsed = await parse_answer(
            answer
        )

        print()
        print("ANSWER COMPLETE")
        print(
            "ELAPSED:",
            result.elapsed_seconds,
        )
        print(
            "RAW LENGTH:",
            len(parsed.raw_text),
        )
        print(
            "CLEAN LENGTH:",
            len(parsed.clean_text),
        )
        print(
            "CITATION COUNT:",
            parsed.citation_count,
        )

        print()
        print("=" * 80)
        print("CLEAN ANSWER")
        print("=" * 80)
        print(parsed.clean_text)

        print()
        print("ANSWER COMPLETE")
        print(
            "ELAPSED:",
            result.elapsed_seconds,
        )
        print(
            "LENGTH:",
            len(result.text),
        )

        print()
        print("=" * 80)
        print("ANSWER")
        print("=" * 80)
        print(result.text)

        screenshot_dir = (
                settings.output_dir
                / "probes"
        )

        screenshot_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        screenshot_path = (
                screenshot_dir
                / (
                        "quick_answer_"
                        + datetime.now().strftime(
                    "%Y%m%d_%H%M%S"
                )
                        + ".png"
                )
        )

        await page.screenshot(
            path=str(screenshot_path),
            full_page=True,
        )

        print()
        print(
            "SCREENSHOT:",
            screenshot_path,
        )

        input(
            "验证完成，按 Enter 关闭..."
        )


if __name__ == "__main__":
    asyncio.run(main())
