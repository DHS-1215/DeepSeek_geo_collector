import asyncio

from app.browser.session import BrowserSession
from app.core.config import load_settings


async def main():
    settings = load_settings()

    async with BrowserSession(settings) as session:
        page = session.page

        await page.goto(settings.deepseek_url)
        await page.wait_for_timeout(3000)

        buttons = page.locator(
            '[role="button"]:visible'
        )

        count = await buttons.count()

        print("=" * 80)
        print("VISIBLE BUTTON DOM")
        print("=" * 80)
        print("COUNT:", count)

        for i in range(count):
            item = buttons.nth(i)

            print()
            print("=" * 80)
            print(f"BUTTON #{i}")
            print("=" * 80)

            try:
                html = await item.evaluate(
                    "(el) => el.outerHTML"
                )

                parent_html = await item.evaluate(
                    """
                    (el) => el.parentElement
                        ? el.parentElement.outerHTML
                        : null
                    """
                )

                print("OUTER HTML:")
                print(html)

                print()
                print("PARENT HTML:")
                print(parent_html)

            except Exception as exc:
                print(
                    "ERROR:",
                    repr(exc),
                )


if __name__ == "__main__":
    asyncio.run(main())
