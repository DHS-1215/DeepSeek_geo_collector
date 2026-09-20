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


def test_set_expert_mode_sets_expected_toggles(
        monkeypatch,
):
    page = MagicMock()
    deepseek = DeepSeekPage(page)

    smart_search = MagicMock()
    deep_think = MagicMock()

    set_toggle = AsyncMock()

    monkeypatch.setattr(
        deepseek,
        "_set_toggle",
        set_toggle,
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
        deepseek.set_expert_mode()
    )

    assert (
            set_toggle.await_args_list
            == [
                call(
                    deep_think,
                    True,
                ),
                call(
                    smart_search,
                    False,
                ),
            ]
    )


def test_set_quick_mode_sets_expected_toggles(
        monkeypatch,
):
    page = MagicMock()
    deepseek = DeepSeekPage(page)

    smart_search = MagicMock()
    deep_think = MagicMock()

    set_toggle = AsyncMock()

    monkeypatch.setattr(
        deepseek,
        "_set_toggle",
        set_toggle,
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

    assert (
            set_toggle.await_args_list
            == [
                call(
                    smart_search,
                    True,
                ),
                call(
                    deep_think,
                    False,
                ),
            ]
    )


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
