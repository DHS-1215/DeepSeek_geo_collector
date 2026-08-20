import argparse
import asyncio
from time import monotonic

from app.browser.session import BrowserSession
from app.core.config import load_settings
from app.deepseek.page import DeepSeekPage


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--question",
        required=True,
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=360.0,
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

        quick_mode = (
            await deepseek
            .quick_main_mode()
            .get_attribute(
                "aria-checked"
            )
        )

        expert_mode = (
            await deepseek
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

        previous_answer_count = await (
            deepseek
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

        print()
        print("=" * 80)
        print("EXPERT GENERATION TIMELINE")
        print("=" * 80)

        started_at = monotonic()

        last_text = ""
        stable_since: float | None = None

        reported_stable_marks: set[int] = set()

        while True:
            now = monotonic()
            elapsed = now - started_at

            if elapsed >= args.timeout:
                print()
                print(
                    f"TIMEOUT AFTER "
                    f"{elapsed:.2f}s"
                )
                break

            messages = (
                deepseek
                .assistant_messages()
            )

            count = await messages.count()

            if count > previous_answer_count:
                text = (
                    await messages
                    .last
                    .inner_text()
                )

                if text != last_text:
                    print(
                        f"[{elapsed:7.2f}s] "
                        f"count={count} "
                        f"length={len(text)} "
                        f"delta={len(text) - len(last_text):+d}"
                    )

                    last_text = text
                    stable_since = now

                    reported_stable_marks.clear()

                elif text and stable_since is not None:
                    stable_for = (
                            now - stable_since
                    )

                    for mark in (
                            5,
                            10,
                            15,
                            20,
                            30,
                    ):
                        if (
                                stable_for >= mark
                                and mark
                                not in reported_stable_marks
                        ):
                            print(
                                f"[{elapsed:7.2f}s] "
                                f"TEXT STABLE "
                                f"{mark}s "
                                f"(length={len(text)})"
                            )

                            reported_stable_marks.add(
                                mark
                            )

                    if stable_for >= 30:
                        print()
                        print(
                            "TEXT HAS BEEN STABLE "
                            "FOR 30 SECONDS."
                        )
                        break

            await asyncio.sleep(
                0.5
            )

        print()
        print("=" * 80)
        print("FINAL OBSERVED ANSWER")
        print("=" * 80)
        print(last_text)

        print()
        print(
            "FINAL LENGTH:",
            len(last_text),
        )


if __name__ == "__main__":
    asyncio.run(main())
