from playwright.async_api import (
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

from app.core.config import Settings
from app.core.exceptions import BrowserError


class BrowserSession:
    """管理 Playwright 和浏览器上下文生命周期。"""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

        self._playwright: Playwright | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    @property
    def page(self) -> Page:
        """返回当前页面。"""

        if self._page is None:
            raise BrowserError(
                "Browser session has not been started."
            )

        return self._page

    async def start(self) -> Page:
        """启动持久化 Chromium 浏览器。"""

        if self._context is not None:
            raise BrowserError(
                "Browser session is already started."
            )

        profile_dir = self._settings.browser_profile_dir

        profile_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:
            self._playwright = await async_playwright().start()

            launch_kwargs = {
                "user_data_dir": str(profile_dir),
                "headless": self._settings.headless,
            }

            if self._settings.chromium_executable_path:
                launch_kwargs["executable_path"] = (
                    self._settings.chromium_executable_path
                )

            self._context = (
                await self._playwright.chromium.launch_persistent_context(
                    **launch_kwargs
                )
            )

            if self._context.pages:
                self._page = self._context.pages[0]
            else:
                self._page = await self._context.new_page()

            self._page.set_default_timeout(
                self._settings.default_timeout_seconds * 1000
            )

            return self._page

        except Exception as exc:
            await self.close()

            raise BrowserError(
                f"Failed to start browser session: {exc}"
            ) from exc

    async def close(self) -> None:
        """安全关闭浏览器资源。"""

        try:
            if self._context is not None:
                await self._context.close()
        finally:
            self._context = None
            self._page = None

            if self._playwright is not None:
                await self._playwright.stop()

            self._playwright = None

    async def __aenter__(self) -> "BrowserSession":
        await self.start()
        return self

    async def __aexit__(
            self,
            exc_type,
            exc,
            traceback,
    ) -> None:
        await self.close()
