from urllib.parse import urlparse
from hashlib import sha1

from playwright.async_api import Locator

from app.core.models import GeoSource
from app.deepseek.selectors import (
    SOURCE_CARD,
    SOURCE_CARD_ORDER,
    SOURCE_CARD_SITE_ICON,
    SOURCE_CARD_SNIPPET,
    SOURCE_CARD_TITLE,
)


def build_occurrence_id(
        order: int,
        url: str | None,
) -> str:
    raw = (
        f"deepseek:"
        f"{order}:"
        f"{url or ''}"
    )

    return sha1(
        raw.encode("utf-8")
    ).hexdigest()[:12]


def extract_domain(
        url: str | None,
) -> str | None:
    if not url:
        return None

    parsed = urlparse(url)

    return parsed.netloc or None


async def parse_source_cards(
        cards: Locator,
) -> list[GeoSource]:
    count = await cards.count()

    sources: list[GeoSource] = []

    for index in range(count):
        card = cards.nth(index)

        href = await card.get_attribute(
            "href"
        )

        title_locator = card.locator(
            SOURCE_CARD_TITLE
        )

        snippet_locator = card.locator(
            SOURCE_CARD_SNIPPET
        )

        order_locator = card.locator(
            SOURCE_CARD_ORDER
        )

        title = None
        snippet = None
        order = index + 1
        site_name = None

        if await title_locator.count():
            title = (
                await title_locator
                .inner_text()
            ).strip()

        if await snippet_locator.count():
            snippet = (
                await snippet_locator
                .inner_text()
            ).strip()

            site_locator = card.locator(
                SOURCE_CARD_SITE_ICON
            )

            if await site_locator.count():
                site_name = (
                    await site_locator
                    .first
                    .inner_text()
                ).strip()

        if await order_locator.count():
            raw_order = (
                await order_locator
                .inner_text()
            ).strip()

            if raw_order.isdigit():
                order = int(raw_order)

        source = GeoSource(
            occurrence_id=(
                build_occurrence_id(
                    order,
                    href,
                )
            ),
            order=order,
            site_name=site_name,
            title=title,
            clean_title=title,
            raw_href=href,
            resolved_url=href,
            domain=extract_domain(
                href
            ),
            snippet=snippet,
            source_round=1,
        )

        sources.append(source)

    return sources
