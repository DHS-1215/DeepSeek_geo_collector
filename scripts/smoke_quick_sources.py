import argparse
import asyncio

from app.browser.session import BrowserSession
from app.core.config import load_settings
from app.deepseek.page import DeepSeekPage
from app.deepseek.source_collector import (
    collect_sources,
)


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

        deepseek = DeepSeekPage(
            page
        )

        await deepseek.ensure_ready()

        await deepseek.set_quick_mode()

        print(
            "QUICK MODE:",
            await deepseek
            .quick_main_mode()
            .get_attribute(
                "aria-checked"
            ),
        )

        print(
            "EXPERT MODE:",
            await deepseek
            .expert_main_mode()
            .get_attribute(
                "aria-checked"
            ),
        )

        previous_count = (
            await deepseek
            .assistant_messages()
            .count()
        )

        await deepseek.fill_question(
            args.question
        )

        await deepseek.submit_question()

        print(
            "QUESTION SENT:",
            args.question,
        )

        from app.deepseek.answer_waiter import (
            wait_for_new_answer,
        )

        await wait_for_new_answer(
            page,
            previous_answer_count=(
                previous_count
            ),
            timeout_seconds=(
                settings.quick_max_wait_seconds
            ),
            stable_seconds=5,
        )

        print()
        print("=" * 80)
        print("COLLECT SOURCES")
        print("=" * 80)

        collection = await collect_sources(
            deepseek
        )

        print(
            "STATUS:",
            collection.status.value,
        )

        print(
            "DECLARED COUNT:",
            collection.declared_count,
        )

        print(
            "CAPTURED COUNT:",
            collection.captured_count,
        )

        print(
            "UNIQUE COUNT:",
            collection.unique_count,
        )

        print(
            "COVERAGE:",
            collection.coverage_ratio,
        )

        print()
        print("=" * 80)
        print("SOURCE LIST")
        print("=" * 80)

        for source in collection.sources:
            print()

            print(
                f"[{source.order}]"
            )

            print(
                "SITE:",
                source.site_name,
            )

            print(
                "TITLE:",
                source.title,
            )

            print(
                "URL:",
                source.resolved_url,
            )

            print(
                "DOMAIN:",
                source.domain,
            )

            print(
                "SNIPPET:",
                source.snippet,
            )

        screenshot = (
                settings.output_dir
                / "probes"
                / "quick_sources_smoke.png"
        )

        screenshot.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        await page.screenshot(
            path=str(screenshot),
            full_page=True,
        )

        print()
        print(
            "SCREENSHOT:",
            screenshot,
        )

        input(
            "验证完成，按 Enter 关闭..."
        )


if __name__ == "__main__":
    asyncio.run(main())
