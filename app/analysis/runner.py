from app.analysis.mention_aggregator import (
    analyze_batch_mentions,
)
from app.analysis.models import (
    GeoAnalysisResult,
    MentionTarget,
)
from app.analysis.sentiment_aggregator import (
    analyze_batch_sentiment_with_provider,
)
from app.analysis.sentiment_config import (
    SentimentConfig,
)
from app.analysis.sentiment_providers import (
    SentimentModelProvider,
)
from app.analysis.source_top10 import (
    analyze_source_top10,
)
from app.core.enums import GeoMode
from app.core.models import GeoRunResult


async def run_geo_analysis(
        *,
        results: list[GeoRunResult],
        targets: list[MentionTarget],
        sentiment_provider: SentimentModelProvider,
        sentiment_config: SentimentConfig,
        source_mode: GeoMode = GeoMode.QUICK,
) -> GeoAnalysisResult:
    """
    执行一次完整 GEO Analysis。

    当前分析链：

        GeoRunResult[]
             ↓
        Mention Analysis
             ↓
        Sentiment Analysis
             ↓
        Source Top10
             ↓
        GeoAnalysisResult

    三项核心业务指标分别由已有模块负责：

    提及率：
        mentioned valid answers
        /
        valid answers

    中正率：
        positive + neutral
        /
        successfully classified mentions

    Source Top10 信源率：
        top10 occurrences
        /
        total valid source occurrences

    本 Runner 只负责编排，
    不重复实现任何业务公式。
    """

    _validate_analysis_inputs(
        targets=targets,
        source_mode=source_mode,
    )

    mention_result = (
        analyze_batch_mentions(
            results=results,
            targets=targets,
        )
    )

    sentiment_result = (
        await
        analyze_batch_sentiment_with_provider(
            results=results,
            mention_batch=mention_result,
            targets=targets,
            provider=sentiment_provider,
            config=sentiment_config,
        )
    )

    source_result = (
        analyze_source_top10(
            results=results,
            mode=source_mode,
        )
    )

    return GeoAnalysisResult(
        mention=mention_result,
        sentiment=sentiment_result,
        sources=source_result,
        source_mode=source_mode,
    )


def _validate_analysis_inputs(
        *,
        targets: list[MentionTarget],
        source_mode: GeoMode,
) -> None:
    """
    检查统一 Analysis Runner 的输入。
    """

    if not targets:
        raise ValueError(
            "analysis targets cannot be empty"
        )

    if source_mode not in {
        GeoMode.QUICK,
        GeoMode.EXPERT,
    }:
        raise ValueError(
            "unsupported source analysis mode: "
            f"{source_mode!r}"
        )
