import argparse
import asyncio
import json
from datetime import datetime

from app.browser.session import BrowserSession
from app.core.config import load_settings
from app.deepseek.page import DeepSeekPage


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--question",
        required=True,
        help="本次用于 DeepSeek DOM 探测的问题",
    )

    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    settings = load_settings()

    probe_dir = (
            settings.output_dir
            / "probes"
            / datetime.now().strftime(
        "answer_%Y%m%d_%H%M%S"
    )
    )

    probe_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

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

        print(
            "DEEP_THINK:",
            await deepseek
            .deep_think_toggle()
            .get_attribute("aria-pressed"),
        )

        print(
            "SMART_SEARCH:",
            await deepseek
            .smart_search_toggle()
            .get_attribute("aria-pressed"),
        )

        await deepseek.fill_question(
            args.question
        )

        print(
            "QUESTION:",
            args.question,
        )

        await deepseek.submit_question()

        print()
        print("问题已经发送。")
        print(
            "等 DeepSeek 页面上回答完全结束后，"
            "再回到终端按 Enter。"
        )

        input()

        html_path = (
                probe_dir
                / "final.html"
        )

        screenshot_path = (
                probe_dir
                / "final.png"
        )

        elements_path = (
                probe_dir
                / "text_elements.json"
        )

        html_path.write_text(
            await page.content(),
            encoding="utf-8",
        )

        await page.screenshot(
            path=str(screenshot_path),
            full_page=True,
        )

        candidates = await page.locator(
            "div, p, section, article"
        ).evaluate_all(
            """
            elements => elements
                .map((el, index) => {
                    const rect =
                        el.getBoundingClientRect();

                    const style =
                        window.getComputedStyle(el);

                    const text =
                        (el.innerText || "")
                            .trim()
                            .replace(/\\s+/g, " ");

                    return {
                        index,
                        tag:
                            el.tagName.toLowerCase(),
                        class_name:
                            el.className
                                ?.toString()
                                .slice(0, 300)
                            || "",
                        text:
                            text.slice(0, 1000),
                        text_length:
                            text.length,
                        visible:
                            rect.width > 0 &&
                            rect.height > 0 &&
                            style.display !== "none" &&
                            style.visibility !== "hidden"
                    };
                })
                .filter(item =>
                    item.visible &&
                    item.text_length >= 20
                )
                .slice(-50)
            """
        )

        elements_path.write_text(
            json.dumps(
                candidates,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        print()
        print("=" * 80)
        print("FINAL TEXT CANDIDATES")
        print("=" * 80)

        for item in candidates:
            print(
                json.dumps(
                    item,
                    ensure_ascii=False,
                )
            )

        print()
        print("HTML:", html_path)
        print("SCREENSHOT:", screenshot_path)
        print("ELEMENTS:", elements_path)

        input(
            "探针完成，按 Enter 关闭浏览器..."
        )


if __name__ == "__main__":
    asyncio.run(main())
