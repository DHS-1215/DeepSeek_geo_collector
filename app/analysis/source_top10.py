from dataclasses import dataclass, field

from app.analysis.models import (
    SourceRankItem,
    SourceTop10Summary,
)
from app.analysis.validity import (
    is_valid_analysis_answer,
)
from app.core.enums import GeoMode
from app.core.models import (
    GeoRunResult,
    GeoSource,
)
from app.package.source_utils import (
    canonicalize_url,
)


@dataclass(slots=True)
class _SourceAggregate:
    source_key: str

    occurrence_count: int = 0

    question_ids: set[str] = field(
        default_factory=set
    )

    order_total: int = 0

    first_seen_order: int = 0

    title: str | None = None

    site_name: str | None = None

    canonical_url: str | None = None


def analyze_source_top10(
        *,
        results: list[GeoRunResult],
        mode: GeoMode | None,
) -> SourceTop10Summary:
    """
    计算一个 Batch 的 Source Top10。

    业务口径沿用豆包：

    - 只统计有效回答
    - 同一回答内同一标准 source 只算一次
    - 不同回答引用同一 source 累加 occurrence
    - occurrence 是信源占比的分子/分母
    - Top10 信源率 =
        Top10 occurrences / total occurrences

    mode:
        QUICK / EXPERT / None(all)

    DeepSeek 当前正式调用应使用 QUICK。
    """

    aggregates: dict[
        str,
        _SourceAggregate,
    ] = {}

    first_seen_sequence = 0

    for result in results:
        if (
                mode is not None
                and result.task.mode != mode
        ):
            continue

        if not is_valid_analysis_answer(
                result
        ):
            continue

        seen_in_answer: set[str] = set()

        for source in result.sources.sources:
            source_key, canonical_url = (
                _source_identity(
                    source
                )
            )

            if not source_key:
                continue

            # 豆包既有业务规则：
            # 同一回答内相同 source 只算一次。
            if source_key in seen_in_answer:
                continue

            seen_in_answer.add(
                source_key
            )

            first_seen_sequence += 1

            aggregate = aggregates.get(
                source_key
            )

            if aggregate is None:
                aggregate = _SourceAggregate(
                    source_key=source_key,

                    first_seen_order=(
                        first_seen_sequence
                    ),

                    title=(
                            source.clean_title
                            or source.title
                    ),

                    site_name=(
                            source.site_name
                            or source.domain
                    ),

                    canonical_url=(
                            canonical_url
                            or None
                    ),
                )

                aggregates[
                    source_key
                ] = aggregate

            aggregate.occurrence_count += 1

            aggregate.question_ids.add(
                result.task.question_id
            )

            aggregate.order_total += (
                source.order
            )

    total_occurrences = sum(
        item.occurrence_count
        for item in aggregates.values()
    )

    ranked = sorted(
        aggregates.values(),
        key=_ranking_key,
    )

    public_items = [
        _to_public_item(
            item,
            total_occurrences=(
                total_occurrences
            ),
        )
        for item in ranked[:10]
    ]

    top10_occurrences = sum(
        item.occurrence_count
        for item in ranked[:10]
    )

    outside_occurrences = (
            total_occurrences
            - top10_occurrences
    )

    top10_share = (
        top10_occurrences
        / total_occurrences
        if total_occurrences
        else 0.0
    )

    outside_share = (
        outside_occurrences
        / total_occurrences
        if total_occurrences
        else 0.0
    )

    return SourceTop10Summary(
        total_occurrences=(
            total_occurrences
        ),

        top10_occurrences=(
            top10_occurrences
        ),

        top10_share=top10_share,

        outside_top10_occurrences=(
            outside_occurrences
        ),

        outside_top10_share=(
            outside_share
        ),

        items=public_items,
    )


def _source_identity(
        source: GeoSource,
) -> tuple[str, str]:
    """
    生成业务层 source identity。

    优先：
        canonical URL

    URL 不存在时：
        site_name/domain + clean_title/title
    """

    raw_url = (
            source.resolved_url
            or source.raw_href
            or ""
    )

    canonical_url = (
        canonicalize_url(
            raw_url
        )
        if raw_url
        else ""
    )

    if canonical_url:
        return (
            canonical_url,
            canonical_url,
        )

    site_name = _normalize_meta(
        source.site_name
        or source.domain
        or ""
    )

    title = _normalize_meta(
        source.clean_title
        or source.title
        or ""
    )

    if not site_name and not title:
        return "", ""

    return (
        f"{site_name}|{title}",
        "",
    )


def _normalize_meta(
        value: str,
) -> str:
    return " ".join(
        value
        .strip()
        .lower()
        .split()
    )


def _ranking_key(
        item: _SourceAggregate,
) -> tuple[
    int,
    int,
    float,
    int,
    str,
]:
    """
    豆包 Source Top10 排序思想：

    1. occurrence_count 降序
    2. question_count 降序
    3. average_order 升序
    4. first_seen_order 升序
    5. source_key 字典序
    """

    average_order = (
            item.order_total
            / item.occurrence_count
    )

    return (
        -item.occurrence_count,
        -len(item.question_ids),
        average_order,
        item.first_seen_order,
        item.source_key,
    )


def _to_public_item(
        item: _SourceAggregate,
        *,
        total_occurrences: int,
) -> SourceRankItem:
    average_order = (
            item.order_total
            / item.occurrence_count
    )

    share = (
        item.occurrence_count
        / total_occurrences
        if total_occurrences
        else 0.0
    )

    return SourceRankItem(
        source_key=item.source_key,

        occurrence_count=(
            item.occurrence_count
        ),

        question_count=len(
            item.question_ids
        ),

        average_order=average_order,

        first_seen_order=(
            item.first_seen_order
        ),

        share=share,

        title=item.title,

        site_name=item.site_name,

        canonical_url=(
            item.canonical_url
        ),
    )
