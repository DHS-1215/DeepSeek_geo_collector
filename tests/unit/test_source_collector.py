import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.core.enums import (
    SourceCollectionStatus,
)

from app.deepseek.source_collector import (
    extract_declared_count,
    collect_sources,
)


def test_extract_declared_count() -> None:
    assert (
            extract_declared_count(
                "已阅读 11 个网页"
            )
            == 11
    )

    assert (
            extract_declared_count(
                "xxx 已阅读 3 个网页 xxx"
            )
            == 3
    )

    assert (
            extract_declared_count(
                "没有来源"
            )
            == 0
    )


def test_collect_sources_without_indicator() -> None:
    deepseek = MagicMock()

    indicator = MagicMock()

    indicator.count = AsyncMock(
        return_value=0
    )

    deepseek.read_webpages_indicator.return_value = (
        indicator
    )

    result = asyncio.run(
        collect_sources(
            deepseek
        )
    )

    assert (
            result.status
            == SourceCollectionStatus.NOT_APPLICABLE
    )

    assert result.captured_count == 0


def test_collect_sources_success() -> None:
    deepseek = MagicMock()

    deepseek.wait_for = AsyncMock()

    indicator = MagicMock()

    indicator.count = AsyncMock(
        return_value=1
    )

    indicator.nth.return_value = indicator

    indicator.is_visible = AsyncMock(
        return_value=True
    )

    indicator.inner_text = AsyncMock(
        return_value="已阅读 2 个网页"
    )

    indicator.click = AsyncMock()

    deepseek.read_webpages_indicator.return_value = (
        indicator
    )

    cards = MagicMock()

    deepseek.source_cards.return_value = cards

    async def fake_parse_source_cards(
            _,
    ):
        from app.core.models import (
            GeoSource,
        )

        return [
            GeoSource(
                occurrence_id="abc123",
                order=1,
                title="测试1",
                resolved_url=(
                    "https://a.com"
                ),
            ),
            GeoSource(
                occurrence_id="abc456",
                order=2,
                title="测试2",
                resolved_url=(
                    "https://b.com"
                ),
            ),
        ]

    import app.deepseek.source_collector as collector

    old_parser = (
        collector.parse_source_cards
    )

    collector.parse_source_cards = (
        fake_parse_source_cards
    )

    try:
        result = asyncio.run(
            collect_sources(
                deepseek
            )
        )
    finally:
        collector.parse_source_cards = (
            old_parser
        )

    assert (
            result.status
            == SourceCollectionStatus.SUCCESS
    )

    assert (
            result.declared_count
            == 2
    )

    assert (
            result.captured_count
            == 2
    )

    assert (
            result.unique_count
            == 2
    )

    assert (
            result.coverage_ratio
            == 1.0
    )

    indicator.click.assert_awaited_once()
