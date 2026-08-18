import argparse
import asyncio
import json
import time
from datetime import datetime

from app.browser.session import BrowserSession
from app.core.config import load_settings
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

    probe_dir = (
            settings.output_dir
            / "probes"
            / datetime.now().strftime(
        "generation_%Y%m%d_%H%M%S"
    )
    )

    probe_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    timeline_path = probe_dir / "timeline.json"

    async with BrowserSession(settings) as session:
        page = session.page

        await page.goto(
            settings.deepseek_url,
            wait_until="domcontentloaded",
        )

        deepseek = DeepSeekPage(page)

        await deepseek.ensure_ready()
        await deepseek.set_quick_mode()
        await deepseek.fill_question(
            args.question
        )

        before_count = await page.locator(
            ".ds-assistant-message-main-content"
        ).count()

        print(
            "ASSISTANT COUNT BEFORE:",
            before_count,
        )

        await deepseek.submit_question()

        started = time.monotonic()
        timeline = []

        for tick in range(240):
            elapsed = round(
                time.monotonic() - started,
                2,
            )

            answers = page.locator(
                ".ds-assistant-message-main-content"
            )

            answer_count = await answers.count()

            latest_text = ""

            if answer_count > 0:
                latest_text = (
                    await answers.last.inner_text()
                ).strip()

            buttons = await page.locator(
                '[role="button"]:visible'
            ).evaluate_all(
                """
                elements => elements.map(el => ({
                    class_name:
                        el.className?.toString() || "",
                    text:
                        (el.innerText || el.textContent || "")
                            .trim()
                            .replace(/\\s+/g, " "),
                    html:
                        el.outerHTML.slice(0, 500)
                }))
                """
            )

            snapshot = {
                "tick": tick,
                "elapsed": elapsed,
                "answer_count": answer_count,
                "latest_text_length": len(
                    latest_text
                ),
                "latest_text": latest_text,
                "buttons": buttons,
            }

            timeline.append(snapshot)

            print(
                f"{elapsed:>6}s | "
                f"answers={answer_count} | "
                f"length={len(latest_text)}"
            )

            await asyncio.sleep(0.5)

        timeline_path.write_text(
            json.dumps(
                timeline,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        print()
        print(
            "TIMELINE:",
            timeline_path,
        )

        input(
            "探针完成，按 Enter 关闭..."
        )


if __name__ == "__main__":
    asyncio.run(main())
