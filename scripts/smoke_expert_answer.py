import argparse
import asyncio
from datetime import datetime

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
        await deepseek.set_expert_mode()

        # 验证真正的主模式状态
        quick_mode = await (
            deepseek
            .quick_main_mode()
            .get_attribute(
                "aria-checked"
            )
        )

        expert_mode = await (
            deepseek
            .expert_main_mode()
            .get_attribute(
                "aria-checked"
            )
        )

        print(
            "QUICK MODE:",
            quick_mode,
        )

        print(
            "EXPERT MODE:",
            expert_mode,
        )

        # Expert 模式下 DeepThink 仍然存在
        deep_think = (
            deepseek.deep_think_toggle()
        )

        deep_think_count = (
            await deep_think.count()
        )

        print(
            "DEEP_THINK COUNT:",
            deep_think_count,
        )

        if deep_think_count == 1:
            print(
                "DEEP_THINK:",
                await deep_think.get_attribute(
                    "aria-pressed"
                ),
            )

        # Expert 模式下 SmartSearch
        # 当前实测会从 DOM 中消失
        smart_search = (
            deepseek.smart_search_toggle()
        )

        smart_search_count = (
            await smart_search.count()
        )

        print(
            "SMART_SEARCH COUNT:",
            smart_search_count,
        )

        if smart_search_count == 1:
            print(
                "SMART_SEARCH:",
                await smart_search.get_attribute(
                    "aria-pressed"
                ),
            )

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
                settings.expert_max_wait_seconds
            ),
            stable_seconds=10.0,
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
        print("=" * 80)
        print("RAW ANSWER")
        print("=" * 80)
        print(parsed.raw_text)

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
                        "expert_answer_"
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
