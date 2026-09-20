import re

from app.core.enums import (
    SourceCollectionStatus,
)
from app.core.models import (
    SourceCollection,
)
from app.deepseek.page import DeepSeekPage
from app.deepseek.source_parser import (
    parse_source_cards,
)

from app.package.source_utils import (
    normalize_url,
)


def extract_declared_count(
        text: str,
) -> int:
    match = re.search(
        r"已阅读\s*(\d+)\s*个网页",
        text,
    )

    if not match:
        return 0

    return int(
        match.group(1)
    )


async def collect_sources(
        deepseek: DeepSeekPage,
) -> SourceCollection:
    indicator = (
        deepseek
        .read_webpages_indicator()
    )

    if await indicator.count() == 0:
        return SourceCollection(
            status=(
                SourceCollectionStatus
                .NOT_APPLICABLE
            )
        )

    visible_indicator = None

    for index in range(
            await indicator.count()
    ):
        item = indicator.nth(index)

        if await item.is_visible():
            visible_indicator = item
            break

    if visible_indicator is None:
        return SourceCollection(
            status=(
                SourceCollectionStatus
                .FAILED
            )
        )

    text = (
        await visible_indicator
        .inner_text()
    )

    declared_count = (
        extract_declared_count(
            text
        )
    )

    await visible_indicator.click()

    await deepseek.wait_for(
        1000
    )

    sources = await parse_source_cards(
        deepseek.source_cards()
    )

    captured_count = len(
        sources
    )

    if (
            declared_count == 0
            and "搜索到" in text
            and captured_count > 0
    ):
        declared_count = (
            captured_count
        )

    unique_urls = {
        normalize_url(
            source.resolved_url
        )
        for source in sources
        if source.resolved_url
    }

    unique_count = len(
        unique_urls
    )

    if captured_count == 0:
        status = (
            SourceCollectionStatus.FAILED
        )

    elif (
            declared_count
            and captured_count
            < declared_count
    ):
        status = (
            SourceCollectionStatus.PARTIAL
        )

    else:
        status = (
            SourceCollectionStatus.SUCCESS
        )

    coverage_ratio = (
        captured_count
        / declared_count
        if declared_count
        else 0.0
    )

    return SourceCollection(
        status=status,
        declared_count=(
            declared_count
        ),
        captured_count=(
            captured_count
        ),
        unique_count=(
            unique_count
        ),
        coverage_ratio=(
            coverage_ratio
        ),
        sources=sources,
    )
