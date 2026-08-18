import asyncio

from app.browser.session import BrowserSession
from app.core.config import load_settings


async def print_buttons(page, title: str) -> None:
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)

    buttons = page.locator('[role="button"]:visible')

    count = await buttons.count()

    for index in range(count):
        button = buttons.nth(index)

        info = await button.evaluate(
            """
            el => ({
                tag: el.tagName.toLowerCase(),
                role: el.getAttribute("role"),
                aria_label: el.getAttribute("aria-label"),
                title: el.getAttribute("title"),
                text: (el.innerText || el.textContent || "")
                    .trim()
                    .replace(/\\s+/g, " "),
                class_name: el.className?.toString() || "",
                disabled: el.hasAttribute("disabled"),
                aria_disabled: el.getAttribute("aria-disabled"),
                data_attrs: Object.fromEntries(
                    [...el.attributes]
                        .filter(attr => attr.name.startsWith("data-"))
                        .map(attr => [attr.name, attr.value])
                ),
                html: el.outerHTML.slice(0, 1500)
            })
            """
        )

        print()
        print(f"BUTTON #{index}")
        print(info)


async def main() -> None:
    settings = load_settings()

    async with BrowserSession(settings) as session:
        page = session.page

        await page.goto(
            settings.deepseek_url,
            wait_until="domcontentloaded",
        )

        await page.wait_for_timeout(2000)

        textarea = page.locator(
            'textarea[placeholder*="给 DeepSeek 发送消息"]'
        )

        print(
            "TEXTAREA COUNT:",
            await textarea.count(),
        )

        if await textarea.count() != 1:
            raise RuntimeError(
                "DeepSeek textarea could not be uniquely located."
            )

        textarea_info = await textarea.evaluate(
            """
            el => ({
                outer_html: el.outerHTML,
                parent_html: el.parentElement?.outerHTML.slice(0, 3000),
                grandparent_html:
                    el.parentElement?.parentElement?.outerHTML.slice(0, 5000)
            })
            """
        )

        toggles = page.locator(
            ".ds-toggle-button:visible"
        )

        print()
        print("=" * 80)
        print("TOGGLES")
        print("=" * 80)

        for index in range(await toggles.count()):
            toggle = toggles.nth(index)

            info = await toggle.evaluate(
                """
                el => ({
                    text: (el.innerText || el.textContent || "")
                        .trim()
                        .replace(/\\s+/g, " "),
                    aria_pressed: el.getAttribute("aria-pressed"),
                    class_name: el.className?.toString() || "",
                    html: el.outerHTML.slice(0, 1000)
                })
                """
            )

            print(
                f"TOGGLE #{index}:",
                info,
            )

        print()
        print("TEXTAREA:")
        print(textarea_info)

        await print_buttons(
            page,
            "输入内容之前",
        )

        # 只填入测试文本，不发送。
        await textarea.fill(
            "DeepSeek GEO DOM probe - DO NOT SEND"
        )

        await page.wait_for_timeout(500)

        await print_buttons(
            page,
            "输入内容之后",
        )

        # 清空，保证不会误发送。
        await textarea.fill("")

        print()
        print("已清空测试内容，没有发送消息。")

        input(
            "探针完成，按 Enter 关闭浏览器..."
        )


if __name__ == "__main__":
    asyncio.run(main())
