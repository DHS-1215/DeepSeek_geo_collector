import asyncio

from app.browser.session import BrowserSession
from app.core.config import load_settings
from app.core.exceptions import UiChangedError
from app.deepseek.page import DeepSeekPage


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
        await deepseek.set_quick_mode()

        await deepseek.fill_question(
            "DeepSeek GEO W5 Quick smoke test"
        )

        deep_think = await (
            deepseek
            .deep_think_toggle()
            .get_attribute("aria-pressed")
        )

        smart_search = await (
            deepseek
            .smart_search_toggle()
            .get_attribute("aria-pressed")
        )

        print(
            "DEEP_THINK:",
            deep_think,
        )

        print(
            "SMART_SEARCH:",
            smart_search,
        )

        print(
            "INPUT:",
            await deepseek.message_input().input_value(),
        )

        # 清空，不发送。
        await deepseek.message_input().fill("")

        input(
            "验证完成，按 Enter 关闭..."
        )

    async def submit_question(self) -> None:
        """发送当前输入框中的问题。"""

        input_box = self.message_input()

        value = await input_box.input_value()

        if not value.strip():
            raise ValueError(
                "Cannot submit an empty question."
            )

        button = self.send_button()

        if await button.count() != 1:
            raise UiChangedError(
                "DeepSeek send button could not be uniquely located."
            )

        class_name = (
                await button.get_attribute("class")
                or ""
        )

        if "ds-button--disabled" in class_name:
            raise UiChangedError(
                "DeepSeek send button is unexpectedly disabled."
            )

        await button.click()

if __name__ == "__main__":
    asyncio.run(main())
