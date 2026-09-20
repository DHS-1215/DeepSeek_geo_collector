import asyncio

from app.browser.session import BrowserSession
from app.core.config import load_settings


async def main():
    settings = load_settings()

    async with BrowserSession(settings) as session:
        page = session.page

        await page.goto(settings.deepseek_url)
        await page.wait_for_timeout(3000)

        print("=" * 80)
        print("BODY KEYWORDS")
        print("=" * 80)

        body_text = await page.locator("body").inner_text()

        keywords = [
            "快速",
            "专家",
            "识图",
            "深度思考",
            "智能搜索",
            "DeepSeek",
        ]

        lines = [
            line.strip()
            for line in body_text.splitlines()
            if line.strip()
        ]

        for keyword in keywords:
            matched = [
                line
                for line in lines
                if keyword in line
            ]

            print()
            print(
                f"{keyword}: "
                f"{len(matched)}"
            )

            for line in matched[:20]:
                print(
                    "  ",
                    repr(line),
                )

        print()
        print("=" * 80)
        print("VISIBLE ROLE=BUTTON")
        print("=" * 80)

        buttons = page.locator(
            '[role="button"]:visible'
        )

        count = await buttons.count()

        print(
            "VISIBLE BUTTON COUNT:",
            count,
        )

        for i in range(count):
            item = buttons.nth(i)

            try:
                text = (
                    await item.inner_text()
                ).strip().replace(
                    "\n",
                    " | ",
                )

                title = await item.get_attribute(
                    "title"
                )

                data_testid = await item.get_attribute(
                    "data-testid"
                )

                cls = await item.get_attribute(
                    "class"
                )

                print()
                print(
                    f"[{i}] TEXT={text!r}"
                )
                print(
                    f"    title={title!r}"
                )
                print(
                    f"    data-testid="
                    f"{data_testid!r}"
                )
                print(
                    f"    class={cls!r}"
                )

            except Exception as exc:
                print(
                    f"[{i}] ERROR:",
                    repr(exc),
                )


if __name__ == "__main__":
    asyncio.run(main())
