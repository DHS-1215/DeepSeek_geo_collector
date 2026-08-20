import asyncio
import json

from app.browser.session import BrowserSession
from app.core.config import load_settings
from app.deepseek.page import DeepSeekPage

MODE_LABELS = (
    "快速模式",
    "专家模式",
    "识图模式",
)


async def main() -> None:
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

        print("=" * 80)
        print("MAIN MODE DOM PROBE")
        print("=" * 80)

        for label in MODE_LABELS:
            locator = page.get_by_text(
                label,
                exact=True,
            )

            count = await locator.count()

            print()
            print(
                f"{label}: COUNT={count}"
            )

            for index in range(count):
                item = locator.nth(index)

                info = await item.evaluate(
                    """
                    (el) => {
                        const parent = el.parentElement;
                        const grandparent = (
                            parent
                            ? parent.parentElement
                            : null
                        );

                        return {
                            tag: el.tagName,
                            text: el.innerText,
                            class_name: (
                                el.className || ""
                            ),
                            role: el.getAttribute("role"),
                            aria_pressed: (
                                el.getAttribute(
                                    "aria-pressed"
                                )
                            ),
                            aria_selected: (
                                el.getAttribute(
                                    "aria-selected"
                                )
                            ),
                            tabindex: (
                                el.getAttribute(
                                    "tabindex"
                                )
                            ),
                            outer_html: el.outerHTML,
                            parent_html: (
                                parent
                                ? parent.outerHTML
                                : null
                            ),
                            grandparent_html: (
                                grandparent
                                ? grandparent.outerHTML
                                : null
                            ),
                        };
                    }
                    """
                )

                print(
                    json.dumps(
                        info,
                        ensure_ascii=False,
                        indent=2,
                    )
                )

        print()
        print("=" * 80)
        print("CURRENT FUNCTION TOGGLES")
        print("=" * 80)

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

        print()
        print("=" * 80)
        print("SELECT EXPERT MODE")
        print("=" * 80)

        quick_mode = (
            deepseek.quick_main_mode()
        )

        expert_mode = (
            deepseek.expert_main_mode()
        )

        print(
            "QUICK BEFORE:",
            await quick_mode.get_attribute(
                "aria-checked"
            ),
        )

        print(
            "EXPERT BEFORE:",
            await expert_mode.get_attribute(
                "aria-checked"
            ),
        )

        await deepseek._select_main_mode(
            expert_mode
        )

        print()

        print(
            "QUICK AFTER:",
            await quick_mode.get_attribute(
                "aria-checked"
            ),
        )

        print(
            "EXPERT AFTER:",
            await expert_mode.get_attribute(
                "aria-checked"
            ),
        )

        deep_think_after = (
            deepseek.deep_think_toggle()
        )

        deep_think_after_count = (
            await deep_think_after.count()
        )

        print(
            "DEEP_THINK COUNT AFTER:",
            deep_think_after_count,
        )

        if deep_think_after_count == 1:
            print(
                "DEEP_THINK AFTER:",
                await deep_think_after.get_attribute(
                    "aria-pressed"
                ),
            )

        smart_search_after = (
            deepseek.smart_search_toggle()
        )

        smart_search_after_count = (
            await smart_search_after.count()
        )

        print(
            "SMART_SEARCH COUNT AFTER:",
            smart_search_after_count,
        )

        if smart_search_after_count == 1:
            print(
                "SMART_SEARCH AFTER:",
                await smart_search_after.get_attribute(
                    "aria-pressed"
                ),
            )

        input(
            "探针完成，按 Enter 关闭..."
        )


if __name__ == "__main__":
    asyncio.run(main())
