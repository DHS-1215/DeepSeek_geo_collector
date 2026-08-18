import asyncio
import json
from datetime import datetime
from pathlib import Path

from app.browser.session import BrowserSession
from app.core.config import load_settings


async def main() -> None:
    settings = load_settings()

    probe_dir = settings.output_dir / "probes"
    probe_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    html_path = probe_dir / f"deepseek_dom_{timestamp}.html"
    screenshot_path = probe_dir / f"deepseek_dom_{timestamp}.png"
    elements_path = probe_dir / f"deepseek_elements_{timestamp}.json"

    async with BrowserSession(settings) as session:
        page = session.page

        await page.goto(
            settings.deepseek_url,
            wait_until="domcontentloaded",
        )

        # 给前端 SPA 一点渲染时间。
        await page.wait_for_timeout(2000)

        print("URL:", page.url)
        print("TITLE:", await page.title())

        elements = await page.locator(
            """
            textarea,
            input,
            button,
            [contenteditable="true"],
            [role="textbox"],
            [role="button"]
            """
        ).evaluate_all(
            """
            elements => elements.map((el, index) => {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);

                return {
                    index,
                    tag: el.tagName.toLowerCase(),
                    role: el.getAttribute("role"),
                    type: el.getAttribute("type"),
                    placeholder: el.getAttribute("placeholder"),
                    aria_label: el.getAttribute("aria-label"),
                    title: el.getAttribute("title"),
                    text: (el.innerText || el.textContent || "")
                        .trim()
                        .replace(/\\s+/g, " ")
                        .slice(0, 200),
                    class_name: el.className?.toString().slice(0, 300) || "",
                    contenteditable: el.getAttribute("contenteditable"),
                    visible:
                        rect.width > 0 &&
                        rect.height > 0 &&
                        style.visibility !== "hidden" &&
                        style.display !== "none"
                };
            })
            """
        )

        visible_elements = [
            element
            for element in elements
            if element["visible"]
        ]

        print()
        print(
            f"发现交互元素: {len(elements)} 个，"
            f"当前可见: {len(visible_elements)} 个"
        )
        print()

        for element in visible_elements:
            print(
                json.dumps(
                    element,
                    ensure_ascii=False,
                )
            )

        html_path.write_text(
            await page.content(),
            encoding="utf-8",
        )

        elements_path.write_text(
            json.dumps(
                visible_elements,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        await page.screenshot(
            path=str(screenshot_path),
            full_page=True,
        )

        print()
        print("HTML:", html_path)
        print("ELEMENTS:", elements_path)
        print("SCREENSHOT:", screenshot_path)

        input("探针完成，按 Enter 关闭浏览器...")


if __name__ == "__main__":
    asyncio.run(main())
