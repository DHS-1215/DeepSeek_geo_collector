from app.core.enums import (
    GeoMode,
    TaskStatus,
)

from app.core.models import (
    GeoRunResult,
    GeoSource,
    GeoTask,
    SourceCollection,
)

from app.package.models import (
    PackageReadResult,
)

from app.analysis.models import (
    GeoAnalysisResult,
    MentionTarget,
)

from app.analysis.runner import (
    run_geo_analysis,
)

from app.analysis.sentiment_config import (
    SentimentConfig,
)

from app.analysis.sentiment_providers import (
    SentimentModelProvider,
)


def build_replay_results(
        package: PackageReadResult,
) -> list[GeoRunResult]:
    """
    将 geo_package 读取结果转换为
    GEO Analysis 输入。
    """

    task_map = {
        item.task_id: item
        for item in package.tasks
    }

    source_map: dict[
        str,
        list[GeoSource],
    ] = {}

    for source in package.sources:
        source_map.setdefault(
            source.answer_id,
            [],
        ).append(
            GeoSource(
                occurrence_id=(
                    source.occurrence_id
                ),
                order=(
                    source.source_order
                ),
                title=(
                    source.source_title_raw
                ),
                site_name=(
                    source.source_site_name_raw
                ),
                raw_href=(
                    source.raw_href
                ),
                resolved_url=(
                    source.resolved_url
                ),
                domain=(
                    source.domain
                ),
                source_round=(
                    source.search_round
                ),
                is_duplicate=(
                    source.is_duplicate_in_answer
                ),
                snippet=(
                    source.source_snippet
                ),
            )
        )

    results: list[GeoRunResult] = []

    for answer in package.answers:

        task_row = task_map.get(
            answer.task_id
        )

        if task_row is None:
            raise ValueError(
                "unknown task_id: "
                f"{answer.task_id}"
            )

        task = GeoTask(
            task_id=(
                task_row.task_id
            ),
            question_id=(
                task_row.question_id
            ),
            question=(
                task_row.question
            ),
            mode=GeoMode(
                task_row.mode_code
            ),
        )

        answer_sources = (
            source_map.get(
                answer.answer_id,
                [],
            )
        )

        results.append(
            GeoRunResult(
                provider=(
                    package.manifest
                    .platform_code
                ),
                run_id=(
                    answer.answer_id
                ),
                task=task,
                batch_id=(
                    answer.batch_id
                ),
                answer_text_raw=(
                    answer.answer_text_raw
                ),
                answer_text_clean=(
                    answer.answer_text_clean
                ),
                sources=SourceCollection(
                    sources=answer_sources,
                    captured_count=len(
                        answer_sources
                    ),
                    unique_count=len(
                        answer_sources
                    ),
                ),
                status=(
                    TaskStatus.SUCCESS
                ),
            )
        )

    return results


async def replay_analysis(
        *,
        package_path,
        product_id: str,
        product_name: str,
        sentiment_provider: SentimentModelProvider,
        sentiment_config: SentimentConfig,
) -> GeoAnalysisResult:
    """
    从 GEO Package 重新执行 Analysis。
    """

    from app.package.reader import (
        read_geo_package,
    )

    package = read_geo_package(
        package_path
    )

    results = build_replay_results(
        package
    )

    targets = [
        MentionTarget(
            target_id=product_id,
            name=product_name,
            aliases=[
                product_name,
            ],
        )
    ]

    return await run_geo_analysis(
        results=results,
        targets=targets,
        sentiment_provider=(
            sentiment_provider
        ),
        sentiment_config=(
            sentiment_config
        ),
    )
