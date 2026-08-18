from playwright.async_api import Locator, Page

from app.core.exceptions import UiChangedError
from app.deepseek.selectors import (
    DEEP_THINK_TOGGLE,
    MESSAGE_INPUT,
    SEND_BUTTON,
    SMART_SEARCH_TOGGLE,
)

from app.deepseek.selectors import (
    ASSISTANT_MESSAGE_MAIN,
    DEEP_THINK_TOGGLE,
    MESSAGE_INPUT,
    SEND_BUTTON,
    SMART_SEARCH_TOGGLE,
)


class DeepSeekPage:
    """DeepSeek 页面交互封装。"""

    def __init__(self, page: Page) -> None:
        self._page = page

    def message_input(self) -> Locator:
        return self._page.locator(
            MESSAGE_INPUT
        )

    def deep_think_toggle(self) -> Locator:
        return self._page.locator(
            DEEP_THINK_TOGGLE
        )

    def smart_search_toggle(self) -> Locator:
        return self._page.locator(
            SMART_SEARCH_TOGGLE
        )

    async def ensure_ready(self) -> None:
        """确认 DeepSeek 输入区域已经可用。"""

        input_box = self.message_input()

        if await input_box.count() != 1:
            raise UiChangedError(
                "DeepSeek message input could not be uniquely located."
            )

        await input_box.wait_for(
            state="visible"
        )

    async def _set_toggle(
            self,
            toggle: Locator,
            enabled: bool,
    ) -> None:
        """把 toggle 调整到目标状态。"""

        if await toggle.count() != 1:
            raise UiChangedError(
                "DeepSeek toggle could not be uniquely located."
            )

        pressed = await toggle.get_attribute(
            "aria-pressed"
        )

        if pressed not in {"true", "false"}:
            raise UiChangedError(
                "DeepSeek toggle has invalid aria-pressed state."
            )

        current_enabled = pressed == "true"

        if current_enabled == enabled:
            return

        await toggle.click()

        expected = (
            "true"
            if enabled
            else "false"
        )

        await toggle.wait_for(
            state="visible"
        )

        actual = await toggle.get_attribute(
            "aria-pressed"
        )

        if actual != expected:
            raise UiChangedError(
                "DeepSeek toggle state did not change as expected."
            )

    async def set_quick_mode(self) -> None:
        """Quick：搜索开启，深度思考关闭。"""

        await self._set_toggle(
            self.smart_search_toggle(),
            True,
        )

        await self._set_toggle(
            self.deep_think_toggle(),
            False,
        )

    async def set_expert_mode(self) -> None:
        """Expert：搜索开启，深度思考开启。"""

        await self._set_toggle(
            self.smart_search_toggle(),
            True,
        )

        await self._set_toggle(
            self.deep_think_toggle(),
            True,
        )

    async def fill_question(
            self,
            question: str,
    ) -> None:
        if not question.strip():
            raise ValueError(
                "Question must not be empty."
            )

        await self.message_input().fill(
            question
        )

    def send_button(self) -> Locator:
        return self._page.locator(
            SEND_BUTTON
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

    def assistant_messages(self) -> Locator:
        """返回当前页面中的 assistant 正文容器。"""

        return self._page.locator(
            ASSISTANT_MESSAGE_MAIN
        )
