import argparse
import asyncio
import json
import re

from app.browser.session import BrowserSession
from app.core.config import load_settings
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

    async with BrowserSession(settings) as session:
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

        previous_answer_count = (
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

        await wait_for_new_answer(
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

        print()
        print("=" * 80)
        print("ANSWER CITATION LINKS")
        print("=" * 80)

        answer_links = await answer.locator(
            "a"
        ).evaluate_all(
            """
            nodes => nodes.map(
                (node, index) => ({
                    index,
                    text: (
                        node.innerText
                        || node.textContent
                        || ""
                    ).trim(),
                    href:
                        node.getAttribute("href"),
                    class_name:
                        node.className?.toString()
                        || "",
                    html:
                        node.outerHTML.slice(
                            0,
                            1500
                        )
                })
            )
            """
        )

        print(
            json.dumps(
                answer_links,
                ensure_ascii=False,
                indent=2,
            )
        )

        print()
        print("=" * 80)
        print("READ WEBPAGE CANDIDATES")
        print("=" * 80)

        read_candidates = await page.locator(
            "body"
        ).evaluate(
            """
            body => {
                const pattern =
                    /(?:已阅读|搜索到)\\s*\\d+\\s*个网页/;

                const nodes = [
                    ...body.querySelectorAll(
                        "div,span,button"
                    )
                ];

                return nodes
                    .filter(node => {
                        const text = (
                            node.innerText
                            || ""
                        ).trim();

                        if (!pattern.test(text)) {
                            return false;
                        }

                        const rect =
                            node.getBoundingClientRect();

                        return (
                            rect.width > 0
                            && rect.height > 0
                        );
                    })
                    .map((node, index) => ({
                        index,
                        tag: node.tagName,
                        text: (
                            node.innerText
                            || ""
                        ).trim().slice(
                            0,
                            500
                        ),
                        role:
                            node.getAttribute(
                                "role"
                            ),
                        tabindex:
                            node.getAttribute(
                                "tabindex"
                            ),
                        class_name:
                            node.className
                                ?.toString()
                                || "",
                        child_count:
                            node.children.length,
                        width:
                            node.getBoundingClientRect()
                                .width,
                        height:
                            node.getBoundingClientRect()
                                .height,
                        html:
                            node.outerHTML.slice(
                                0,
                                2000
                            )
                    }))
                    .sort(
                        (a, b) =>
                            a.text.length
                            - b.text.length
                    )
                    .slice(0, 20);
            }
            """
        )

        print(
            json.dumps(
                read_candidates,
                ensure_ascii=False,
                indent=2,
            )
        )

        read_locator = page.get_by_text(
            re.compile(
                r"(?:已阅读|搜索到)\s*\d+\s*个网页"
            )
        )

        count = await read_locator.count()

        print()
        print(
            "READ LOCATOR COUNT:",
            count,
        )

        click_target = None

        for index in range(count):
            candidate = (
                read_locator.nth(index)
            )

            if not await candidate.is_visible():
                continue

            text = (
                await candidate.inner_text()
            ).strip()

            print(
                f"CANDIDATE #{index}:",
                repr(text[:300]),
            )

            if re.fullmatch(
                    r"(?:已阅读|搜索到)\s*\d+\s*个网页",
                    text,
            ):
                click_target = candidate
                break

        if click_target is None:
            print()
            print(
                "没有找到可以安全点击的"
                "“已阅读/搜索到 X 个网页”精确元素。"
            )

            input(
                "探针完成，按 Enter 关闭..."
            )
            return

        print()
        print("=" * 80)
        print("BEFORE CLICK VISIBLE LINKS")
        print("=" * 80)

        before_links = await _visible_links(
            page
        )

        print(
            json.dumps(
                before_links,
                ensure_ascii=False,
                indent=2,
            )
        )

        print()
        print(
            "CLICK TARGET:",
            await click_target.inner_text(),
        )

        await click_target.click()

        await page.wait_for_timeout(
            1000
        )

        print()
        print("=" * 80)
        print("AFTER CLICK VISIBLE LINKS")
        print("=" * 80)

        after_links = await _visible_links(
            page
        )

        print(
            json.dumps(
                after_links,
                ensure_ascii=False,
                indent=2,
            )
        )

        before_signatures = {
            (
                item["text"],
                item["href"],
            )
            for item in before_links
        }

        new_links = [
            item
            for item in after_links
            if (
                   item["text"],
                   item["href"],
               )
               not in before_signatures
        ]

        print()
        print("=" * 80)
        print("NEW LINKS AFTER CLICK")
        print("=" * 80)

        print(
            json.dumps(
                new_links,
                ensure_ascii=False,
                indent=2,
            )
        )

        print()
        print("=" * 80)
        print("DIALOG / POPOVER CANDIDATES")
        print("=" * 80)

        panels = await page.locator(
            "body"
        ).evaluate(
            """
            body => {
                const selectors = [
                    '[role="dialog"]',
                    '[role="listbox"]',
                    '[role="menu"]'
                ];

                const candidates = [
                    ...body.querySelectorAll(
                        selectors.join(",")
                    )
                ];

                return candidates
                    .filter(node => {
                        const rect =
                            node.getBoundingClientRect();

                        return (
                            rect.width > 0
                            && rect.height > 0
                        );
                    })
                    .map((node, index) => ({
                        index,
                        tag: node.tagName,
                        role:
                            node.getAttribute(
                                "role"
                            ),
                        text: (
                            node.innerText
                            || ""
                        ).trim().slice(
                            0,
                            5000
                        ),
                        class_name:
                            node.className
                                ?.toString()
                                || "",
                        html:
                            node.outerHTML.slice(
                                0,
                                5000
                            )
                    }));
            }
            """
        )

        print(
            json.dumps(
                panels,
                ensure_ascii=False,
                indent=2,
            )
        )

        screenshot_path = (
                settings.output_dir
                / "probes"
                / "quick_sources_after_click.png"
        )

        screenshot_path.parent.mkdir(
            parents=True,
            exist_ok=True,
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
            "探针完成，按 Enter 关闭..."
        )


async def _visible_links(
        page,
) -> list[dict]:
    return await page.locator(
        "a"
    ).evaluate_all(
        """
        nodes => nodes
            .filter(node => {
                const rect =
                    node.getBoundingClientRect();

                return (
                    rect.width > 0
                    && rect.height > 0
                );
            })
            .map((node, index) => ({
                index,
                text: (
                    node.innerText
                    || node.textContent
                    || ""
                ).trim().slice(
                    0,
                    1000
                ),
                href:
                    node.getAttribute(
                        "href"
                    ),
                class_name:
                    node.className
                        ?.toString()
                        || "",
                html:
                    node.outerHTML.slice(
                        0,
                        1500
                    )
            }))
        """
    )


if __name__ == "__main__":
    asyncio.run(main())

