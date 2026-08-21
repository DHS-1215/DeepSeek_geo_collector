import argparse
import asyncio
import json

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
        await deepseek.set_expert_mode()

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
                settings.expert_max_wait_seconds
            ),
            stable_seconds=10.0,
        )

        answer = (
            deepseek
            .assistant_messages()
            .last
        )

        print()
        print("=" * 80)
        print("ANSWER")
        print("=" * 80)

        print(
            await answer.inner_text()
        )

        print()
        print("=" * 80)
        print("ANSWER LINKS")
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
                    href: node.getAttribute("href"),
                    role: node.getAttribute("role"),
                    class_name:
                        node.className?.toString()
                        || "",
                    outer_html:
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
        print("ANSWER ANCESTORS")
        print("=" * 80)

        ancestors = await answer.evaluate(
            """
            el => {
                const result = [];
                let current = el;

                for (
                    let level = 0;
                    level < 7 && current;
                    level++
                ) {
                    result.push({
                        level,
                        tag: current.tagName,
                        class_name:
                            current.className
                                ?.toString()
                                || "",
                        text: (
                            current.innerText
                            || ""
                        ).slice(
                            0,
                            3000
                        ),
                        html: (
                            current.outerHTML
                            || ""
                        ).slice(
                            0,
                            5000
                        )
                    });

                    current =
                        current.parentElement;
                }

                return result;
            }
            """
        )

        for item in ancestors:
            print()
            print(
                f"ANCESTOR LEVEL "
                f"{item['level']}"
            )

            print(
                json.dumps(
                    item,
                    ensure_ascii=False,
                    indent=2,
                )
            )

        print()
        print("=" * 80)
        print("SOURCE-LIKE TEXT ELEMENTS")
        print("=" * 80)

        source_like = await page.locator(
            "body"
        ).evaluate(
            """
            body => {
                const keywords = [
                    "已阅读",
                    "网页",
                    "来源",
                    "参考",
                    "搜索",
                    "引用"
                ];

                const nodes = [
                    ...body.querySelectorAll(
                        "div,span,button,a"
                    )
                ];

                return nodes
                    .filter(node => {
                        const text = (
                            node.innerText
                            || ""
                        ).trim();

                        if (!text) {
                            return false;
                        }

                        return keywords.some(
                            keyword =>
                                text.includes(
                                    keyword
                                )
                        );
                    })
                    .filter(node => {
                        const rect =
                            node.getBoundingClientRect();

                        return (
                            rect.width > 0
                            && rect.height > 0
                        );
                    })
                    .slice(0, 100)
                    .map((node, index) => ({
                        index,
                        tag: node.tagName,
                        text: (
                            node.innerText
                            || ""
                        ).trim().slice(
                            0,
                            1000
                        ),
                        href:
                            node.getAttribute(
                                "href"
                            ),
                        role:
                            node.getAttribute(
                                "role"
                            ),
                        class_name:
                            node.className
                                ?.toString()
                                || "",
                        outer_html:
                            node.outerHTML.slice(
                                0,
                                1500
                            )
                    }));
            }
            """
        )

        for item in source_like:
            print(
                json.dumps(
                    item,
                    ensure_ascii=False,
                )
            )

        print()
        print("=" * 80)
        print("PAGE LINKS NEAR ANSWER")
        print("=" * 80)

        nearby_links = await answer.evaluate(
            """
            el => {
                let root = el;

                for (
                    let i = 0;
                    i < 4
                    && root.parentElement;
                    i++
                ) {
                    root =
                        root.parentElement;
                }

                return [
                    ...root.querySelectorAll("a")
                ].map((node, index) => ({
                    index,
                    text: (
                        node.innerText
                        || node.textContent
                        || ""
                    ).trim(),
                    href:
                        node.getAttribute("href"),
                    class_name:
                        node.className
                            ?.toString()
                            || "",
                    outer_html:
                        node.outerHTML.slice(
                            0,
                            1500
                        )
                }));
            }
            """
        )

        print(
            json.dumps(
                nearby_links,
                ensure_ascii=False,
                indent=2,
            )
        )

        input(
            "探针完成，按 Enter 关闭..."
        )


if __name__ == "__main__":
    asyncio.run(main())
