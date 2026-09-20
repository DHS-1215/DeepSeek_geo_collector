import asyncio

from app.browser.session import BrowserSession
from app.core.config import load_settings
from app.deepseek.answer_parser import parse_answer
from app.deepseek.answer_waiter import wait_for_new_answer
from app.deepseek.page import DeepSeekPage


QUESTION = "鸿茅药酒是正规药品吗？需要医生处方吗？"


async def set_toggle(locator, expected: bool) -> None:
    count = await locator.count()

    if count != 1:
        raise RuntimeError(
            f"toggle count must be 1, got {count}"
        )

    current = await locator.get_attribute(
        "aria-pressed"
    )

    if current not in {
        "true",
        "false",
    }:
        raise RuntimeError(
            "invalid aria-pressed: "
            f"{current!r}"
        )

    expected_text = (
        "true"
        if expected
        else "false"
    )

    if current == expected_text:
        return

    await locator.click()

    actual = await locator.get_attribute(
        "aria-pressed"
    )

    if actual != expected_text:
        raise RuntimeError(
            "toggle state change failed: "
            f"expected={expected_text}, "
            f"actual={actual}"
        )


async def run_case(
    *,
    name: str,
    deep_think: bool,
    smart_search: bool,
    timeout_seconds: float,
) -> None:
    settings = load_settings()

    print()
    print("=" * 80)
    print(name)
    print("=" * 80)

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

        await set_toggle(
            deepseek.deep_think_toggle(),
            deep_think,
        )

        await set_toggle(
            deepseek.smart_search_toggle(),
            smart_search,
        )

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

        previous_count = (
            await deepseek
            .assistant_messages()
            .count()
        )

        await deepseek.fill_question(
            QUESTION
        )

        await deepseek.submit_question()

        await wait_for_new_answer(
            page,
            previous_answer_count=(
                previous_count
            ),
            timeout_seconds=(
                timeout_seconds
            ),
            stable_seconds=10.0,
        )

        answer = (
            deepseek
            .assistant_messages()
            .last
        )

        parsed = await parse_answer(
            answer
        )

        link_count = await (
            answer.locator("a").count()
        )

        parent = answer.locator(
            "xpath=.."
        )

        parent_text = ""

        if await parent.count() == 1:
            parent_text = (
                await parent.inner_text()
            )

        print()
        print("ANSWER LENGTH:")
        print(
            len(
                parsed.clean_text
            )
        )

        print()
        print("ANSWER:")
        print(
            parsed.clean_text
        )

        print()
        print("ANSWER LINK COUNT:")
        print(
            link_count
        )

        print()
        print("BEHAVIOR MARKERS:")
        print(
            "已思考:",
            "已思考" in parent_text,
        )
        print(
            "已阅读:",
            "已阅读" in parent_text,
        )
        print(
            "专家模式暂不支持搜索:",
            (
                "专家模式暂不支持搜索"
                in parent_text
            ),
        )

        print()
        print("PARENT TEXT PREVIEW:")
        print(
            parent_text[:1500]
        )


async def main() -> None:
    settings = load_settings()

    await run_case(
        name=(
            "CASE A - QUICK CANDIDATE "
            "(deep_think=false, "
            "smart_search=true)"
        ),
        deep_think=False,
        smart_search=True,
        timeout_seconds=(
            settings.quick_max_wait_seconds
        ),
    )

    await run_case(
        name=(
            "CASE B - EXPERT CANDIDATE "
            "(deep_think=true, "
            "smart_search=false)"
        ),
        deep_think=True,
        smart_search=False,
        timeout_seconds=(
            settings.expert_max_wait_seconds
        ),
    )


if __name__ == "__main__":
    asyncio.run(main())
