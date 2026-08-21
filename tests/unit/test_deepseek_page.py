import asyncio
from unittest.mock import AsyncMock, MagicMock, call

import pytest

from app.core.exceptions import UiChangedError
from app.deepseek.page import DeepSeekPage


def test_select_main_mode_skips_click_when_already_checked():
    page = MagicMock()
    deepseek = DeepSeekPage(page)

    mode = MagicMock()

    mode.count = AsyncMock(
        return_value=1
    )

    mode.get_attribute = AsyncMock(
        return_value="true"
    )

    mode.click = AsyncMock()

    asyncio.run(
        deepseek._select_main_mode(
            mode
        )
    )

    mode.click.assert_not_awaited()


def test_select_main_mode_clicks_when_not_checked():
    page = MagicMock()
    deepseek = DeepSeekPage(page)

    mode = MagicMock()

    mode.count = AsyncMock(
        return_value=1
    )

    mode.get_attribute = AsyncMock(
        side_effect=[
            "false",
            "true",
        ]
    )

    mode.click = AsyncMock()

    asyncio.run(
        deepseek._select_main_mode(
            mode
        )
    )

    mode.click.assert_awaited_once()


def test_select_main_mode_rejects_non_unique_locator():
    page = MagicMock()
    deepseek = DeepSeekPage(page)

    mode = MagicMock()

    mode.count = AsyncMock(
        return_value=0
    )

    with pytest.raises(
            UiChangedError
    ):
        asyncio.run(
            deepseek._select_main_mode(
                mode
            )
        )


def test_select_main_mode_rejects_invalid_state():
    page = MagicMock()
    deepseek = DeepSeekPage(page)

    mode = MagicMock()

    mode.count = AsyncMock(
        return_value=1
    )

    mode.get_attribute = AsyncMock(
        return_value=None
    )

    with pytest.raises(
            UiChangedError
    ):
        asyncio.run(
            deepseek._select_main_mode(
                mode
            )
        )


def test_select_main_mode_rejects_failed_transition():
    page = MagicMock()
    deepseek = DeepSeekPage(page)

    mode = MagicMock()

    mode.count = AsyncMock(
        return_value=1
    )

    mode.get_attribute = AsyncMock(
        side_effect=[
            "false",
            "false",
        ]
    )

    mode.click = AsyncMock()

    with pytest.raises(
            UiChangedError
    ):
        asyncio.run(
            deepseek._select_main_mode(
                mode
            )
        )

    mode.click.assert_awaited_once()


def test_set_expert_mode_selects_expert_main_mode_only(
        monkeypatch,
):
    page = MagicMock()
    deepseek = DeepSeekPage(page)

    expert_mode = MagicMock()

    select_main_mode = AsyncMock()

    monkeypatch.setattr(
        deepseek,
        "_select_main_mode",
        select_main_mode,
    )

    monkeypatch.setattr(
        deepseek,
        "expert_main_mode",
        MagicMock(
            return_value=expert_mode
        ),
    )

    smart_search_toggle = MagicMock()
    deep_think_toggle = MagicMock()

    monkeypatch.setattr(
        deepseek,
        "smart_search_toggle",
        smart_search_toggle,
    )

    monkeypatch.setattr(
        deepseek,
        "deep_think_toggle",
        deep_think_toggle,
    )

    asyncio.run(
        deepseek.set_expert_mode()
    )

    select_main_mode.assert_awaited_once_with(
        expert_mode
    )

    smart_search_toggle.assert_not_called()
    deep_think_toggle.assert_not_called()


def test_set_quick_mode_selects_main_mode_and_toggles(
        monkeypatch,
):
    page = MagicMock()
    deepseek = DeepSeekPage(page)

    quick_mode = MagicMock()
    smart_search = MagicMock()
    deep_think = MagicMock()

    select_main_mode = AsyncMock()
    set_toggle = AsyncMock()

    monkeypatch.setattr(
        deepseek,
        "_select_main_mode",
        select_main_mode,
    )

    monkeypatch.setattr(
        deepseek,
        "_set_toggle",
        set_toggle,
    )

    monkeypatch.setattr(
        deepseek,
        "quick_main_mode",
        MagicMock(
            return_value=quick_mode
        ),
    )

    monkeypatch.setattr(
        deepseek,
        "smart_search_toggle",
        MagicMock(
            return_value=smart_search
        ),
    )

    monkeypatch.setattr(
        deepseek,
        "deep_think_toggle",
        MagicMock(
            return_value=deep_think
        ),
    )

    asyncio.run(
        deepseek.set_quick_mode()
    )

    select_main_mode.assert_awaited_once_with(
        quick_mode
    )

    assert set_toggle.await_args_list == [
        call(
            smart_search,
            True,
        ),
        call(
            deep_think,
            False,
        ),
    ]


def test_source_cards_returns_locator():
    page = MagicMock()

    deepseek = DeepSeekPage(page)

    locator = deepseek.source_cards()

    page.locator.assert_called_once()


def test_read_webpages_indicator_returns_locator():
    page = MagicMock()

    deepseek = DeepSeekPage(page)

    deepseek.read_webpages_indicator()

    page.get_by_text.assert_called_once()
