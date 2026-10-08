import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.deepseek.source_parser import (
    build_occurrence_id,
    extract_domain,
    parse_source_cards,
)


def test_extract_domain() -> None:
    assert (
            extract_domain(
                "https://example.com/page?id=1"
            )
            == "example.com"
    )

    assert (
            extract_domain(
                "http://health.people.com.cn/test"
            )
            == "health.people.com.cn"
    )

    assert extract_domain(None) is None
    assert extract_domain("") is None


def test_build_occurrence_id_is_stable() -> None:
    first = build_occurrence_id(
        2,
        "https://example.com/page",
    )

    second = build_occurrence_id(
        2,
        "https://example.com/page",
    )

    other = build_occurrence_id(
        3,
        "https://example.com/page",
    )

    assert first == second
    assert len(first) == 12
    assert first != other


def test_parse_source_cards_maps_geo_source() -> None:
    cards = MagicMock()

    cards.count = AsyncMock(
        return_value=1
    )

    card = MagicMock()

    cards.nth.return_value = card

    card.get_attribute = AsyncMock(
        return_value=(
            "https://example.com/page?id=1"
        )
    )

    title_locator = MagicMock()
    title_locator.count = AsyncMock(
        return_value=1
    )
    title_locator.inner_text = AsyncMock(
        return_value=" 测试来源标题 "
    )

    snippet_locator = MagicMock()
    snippet_locator.count = AsyncMock(
        return_value=1
    )
    snippet_locator.inner_text = AsyncMock(
        return_value=" 测试来源摘要 "
    )

    order_locator = MagicMock()

    site_locator = MagicMock()

    site_locator.count = AsyncMock(
        return_value=1
    )

    site_locator.first.inner_text = AsyncMock(
        return_value="测试站点"
    )



    order_locator.count = AsyncMock(
        return_value=1
    )
    order_locator.inner_text = AsyncMock(
        return_value="1"
    )

    def locator_side_effect(
            selector: str,
    ):
        from app.deepseek.selectors import (
            SOURCE_CARD_ORDER,
            SOURCE_CARD_SNIPPET,
            SOURCE_CARD_TITLE,
            SOURCE_CARD_SITE_ICON,
        )

        mapping = {
            SOURCE_CARD_TITLE:
                title_locator,

            SOURCE_CARD_SNIPPET:
                snippet_locator,

            SOURCE_CARD_ORDER:
                order_locator,

            SOURCE_CARD_SITE_ICON:
                site_locator,
        }

        return mapping[selector]

    card.locator.side_effect = (
        locator_side_effect
    )

    sources = asyncio.run(
        parse_source_cards(cards)
    )

    assert len(sources) == 1

    source = sources[0]

    assert source.order == 1

    assert (
            source.title
            == "测试来源标题"
    )

    assert (
            source.clean_title
            == "测试来源标题"
    )

    assert (
            source.snippet
            == "测试来源摘要"
    )

    assert (
            source.raw_href
            == "https://example.com/page?id=1"
    )

    assert (
            source.resolved_url
            == "https://example.com/page?id=1"
    )

    assert (
            source.domain
            == "example.com"
    )

    assert source.source_round == 1
    assert len(source.occurrence_id) == 12


def test_parse_source_cards_uses_position_when_order_missing() -> None:
    cards = MagicMock()

    cards.count = AsyncMock(
        return_value=1
    )

    card = MagicMock()
    cards.nth.return_value = card

    card.get_attribute = AsyncMock(
        return_value=(
            "https://example.com/source"
        )
    )

    title_locator = MagicMock()

    title_locator.count = AsyncMock(
        return_value=1
    )

    title_locator.inner_text = AsyncMock(
        return_value="测试来源标题"
    )

    snippet_locator = MagicMock()

    snippet_locator.count = AsyncMock(
        return_value=1
    )

    snippet_locator.inner_text = AsyncMock(
        return_value="测试来源摘要"
    )

    order_locator = MagicMock()

    order_locator.count = AsyncMock(
        return_value=0
    )

    site_locator = MagicMock()

    site_locator.count = AsyncMock(
        return_value=1
    )

    site_locator.first.inner_text = AsyncMock(
        return_value="测试站点"
    )

    def locator_side_effect(
            selector: str,
    ):
        from app.deepseek.selectors import (
            SOURCE_CARD_ORDER,
            SOURCE_CARD_SNIPPET,
            SOURCE_CARD_SITE_ICON,
            SOURCE_CARD_TITLE,
        )

        mapping = {
            SOURCE_CARD_TITLE:
                title_locator,

            SOURCE_CARD_SNIPPET:
                snippet_locator,

            SOURCE_CARD_ORDER:
                order_locator,

            SOURCE_CARD_SITE_ICON:
                site_locator,
        }

        return mapping[selector]

    card.locator.side_effect = (
        locator_side_effect
    )

    sources = asyncio.run(
        parse_source_cards(cards)
    )

    assert len(sources) == 1

    source = sources[0]

    assert source.order == 1
    assert source.title == "测试来源标题"
    assert (
            source.site_name
            == "测试站点"
    )
    assert source.snippet == "测试来源摘要"
    assert source.domain == "example.com"



def test_parse_source_cards_uses_dom_position_when_display_order_conflicts() -> None:
    cards = MagicMock()

    cards.count = AsyncMock(
        return_value=2
    )

    def make_card(
            href: str,
            raw_order: str | None,
    ):
        card = MagicMock()

        card.get_attribute = AsyncMock(
            return_value=href
        )

        title_locator = MagicMock()
        title_locator.count = AsyncMock(
            return_value=0
        )

        snippet_locator = MagicMock()
        snippet_locator.count = AsyncMock(
            return_value=0
        )

        order_locator = MagicMock()

        if raw_order is None:
            order_locator.count = AsyncMock(
                return_value=0
            )
        else:
            order_locator.count = AsyncMock(
                return_value=1
            )
            order_locator.inner_text = AsyncMock(
                return_value=raw_order
            )

        def locator_side_effect(
                selector: str,
        ):
            from app.deepseek.selectors import (
                SOURCE_CARD_ORDER,
                SOURCE_CARD_SNIPPET,
                SOURCE_CARD_TITLE,
            )

            mapping = {
                SOURCE_CARD_TITLE:
                    title_locator,
                SOURCE_CARD_SNIPPET:
                    snippet_locator,
                SOURCE_CARD_ORDER:
                    order_locator,
            }

            return mapping[selector]

        card.locator.side_effect = (
            locator_side_effect
        )

        return card

    first_card = make_card(
        "https://example.com/first",
        None,
    )

    second_card = make_card(
        "https://example.com/second",
        "1",
    )

    cards.nth.side_effect = [
        first_card,
        second_card,
    ]

    sources = asyncio.run(
        parse_source_cards(cards)
    )

    assert len(sources) == 2

    assert [
        source.order
        for source in sources
    ] == [
        1,
        2,
    ]
