from pathlib import Path

from app.analysis.exporter import (
    export_analysis_json,
)

from app.analysis.export_serialization import (
    build_analysis_document,
)

from app.analysis.verifier import (
    verify_analysis_file,
)

from app.analysis.models import (
    GeoAnalysisResult,
    MentionTarget,
    SentimentStatus,
)
from app.analysis.runner import (
    run_geo_analysis,
)
from app.analysis.sentiment_config import (
    SentimentConfig,
    load_sentiment_config,
)
from app.analysis.sentiment_providers import (
    SentimentModelProvider,
    create_sentiment_provider,
)
from app.batch.export import (
    export_batch_package,
)
from app.batch.loader import (
    load_batch_tasks,
)
from app.batch.runner import (
    run_batch,
)
from app.core.enums import GeoMode
from app.package.verifier import (
    verify_geo_package,
)
from app.pipeline.models import (
    PipelineResult,
    PipelineStatus,
)


async def run_collection_pipeline(
        *,
        csv_path: Path,
        batch_id: str,
        output_dir: Path,
        product_id: str,
        product_name: str,
        sentiment_provider: (
                SentimentModelProvider | None
        ) = None,
        sentiment_config: (
                SentimentConfig | None
        ) = None,
) -> PipelineResult:
    """
    执行完整的 DeepSeek GEO Pipeline。

    正式流程：

        LOAD
          ↓
        COLLECT
          ↓
        ANALYZE
          ├─ Mention / 提及率
          ├─ Sentiment / 中正率
          └─ Source Top10 / 信源率
          ↓
        PACKAGE
          ↓
        VERIFY

    sentiment_provider / sentiment_config
    支持依赖注入，方便测试。

    正常 CLI 调用时不传，
    Pipeline 自动读取正式配置并创建 Provider。
    """

    tasks = load_batch_tasks(
        csv_path=csv_path,
        batch_id=batch_id,
    )

    if not tasks:
        raise ValueError(
            "Batch CSV contains no tasks."
        )

    targets = build_analysis_targets(
        product_id=product_id,
        product_name=product_name,
    )

    analysis_config = (
        sentiment_config
        if sentiment_config is not None
        else load_sentiment_config()
    )

    analysis_provider = (
        sentiment_provider
        if sentiment_provider is not None
        else create_sentiment_provider(
            analysis_config
        )
    )

    batch_result = await run_batch(
        tasks
    )

    analysis_result = await run_geo_analysis(
        results=batch_result.results,
        targets=targets,
        sentiment_provider=(
            analysis_provider
        ),
        sentiment_config=(
            analysis_config
        ),
        source_mode=GeoMode.QUICK,
    )

    package_path = export_batch_package(
        result=batch_result,
        output_dir=output_dir,
        product_id=product_id,
        product_name=product_name,
    )

    verify_geo_package(
        package_path
    )

    analysis_document = build_analysis_document(
        batch_id=batch_id,
        product_id=product_id,
        product_name=product_name,
        analysis=analysis_result,
        results=batch_result.results,
    )

    analysis_path = (
            output_dir
            /
            f"geo_analysis_{batch_id}.json"
    )

    export_analysis_json(
        document=analysis_document,
        output_path=analysis_path,
    )

    analysis_verification = verify_analysis_file(
        analysis_path
    )

    if not analysis_verification.passed:
        raise ValueError(
            "analysis verification failed: "
            +
            "; ".join(
                analysis_verification.errors
            )
        )

    status = (
        PipelineStatus.PASS_WITH_WARNINGS
        if (
                batch_result.failed_count > 0
                or _analysis_has_warnings(
            analysis_result
        )
        )
        else PipelineStatus.PASS
    )

    return PipelineResult(
        status=status,
        batch_result=batch_result,
        analysis_result=analysis_result,
        package_path=package_path,
        package_verified=True,
        analysis_path=analysis_path,
        analysis_verified=True,
    )


def build_analysis_targets(
        *,
        product_id: str,
        product_name: str,
) -> list[MentionTarget]:
    """
    根据 Pipeline 产品参数构造默认 GEO 分析目标。

    当前 Pipeline 一次分析一个目标产品。

    默认 aliases 至少包含 product_name。

    后续 CLI 可以继续扩展：
        --product-alias
    """

    normalized_id = (
        product_id.strip()
    )

    normalized_name = (
        product_name.strip()
    )

    if not normalized_id:
        raise ValueError(
            "product_id cannot be empty"
        )

    if not normalized_name:
        raise ValueError(
            "product_name cannot be empty"
        )

    return [
        MentionTarget(
            target_id=normalized_id,
            name=normalized_name,
            aliases=[
                normalized_name,
            ],
        )
    ]


def _analysis_has_warnings(
        analysis_result: GeoAnalysisResult,
) -> bool:
    """
    判断 Analysis 是否存在需要提升
    Pipeline 状态为 PASS_WITH_WARNINGS
    的问题。

    当前规则：

    以下 Sentiment 状态属于正常结果：
    - SUCCESS
    - SUCCESS_WITH_WARNINGS
    - NOT_APPLICABLE

    以下情况属于分析失败：
    - FAILED
    - RATE_LIMITED
    - TIMEOUT

    提及率和 Source Top10 当前都是本地确定性分析，
    不单独产生 Pipeline Warning。
    """

    acceptable_statuses = {
        SentimentStatus.SUCCESS,
        SentimentStatus.SUCCESS_WITH_WARNINGS,
        SentimentStatus.NOT_APPLICABLE,
    }

    for task_results in (
            analysis_result
                    .sentiment
                    .details
                    .values()
    ):
        for sentiment in (
                task_results.values()
        ):
            if (
                    sentiment.status
                    not in acceptable_statuses
            ):
                return True

    return False
