import asyncio
from app.analysis.models import (
    MentionBatchResult,
    MentionTarget,
    SentimentBatchResult,
    SentimentLabel,
    SentimentResult,
    SentimentStatus,
    SentimentSummary,
    TargetSentimentSummary,
)
from app.analysis.sentiment import (
    SentimentClassifier,
    analyze_sentiment,
    analyze_sentiment_with_provider,
)
from app.analysis.sentiment_config import (
    SentimentConfig,
)
from app.analysis.sentiment_providers import (
    RETRYABLE_SENTIMENT_ERROR_TYPES,
    SentimentModelProvider,
)
from app.core.enums import GeoMode
from app.core.models import GeoRunResult

SUCCESS_STATUSES = {
    SentimentStatus.SUCCESS,
    SentimentStatus.SUCCESS_WITH_WARNINGS,
}


async def analyze_batch_sentiment(
        *,
        results: list[GeoRunResult],
        mention_batch: MentionBatchResult,
        targets: list[MentionTarget],
        classifier: SentimentClassifier,
) -> SentimentBatchResult:
    """
    对一个 Batch 执行情感分析并生成汇总。

    保持豆包既有四套统计口径：
    - quick
    - expert
    - all_answers
    - question_level
    """

    _validate_targets(
        targets
    )

    details: dict[
        str,
        dict[
            str,
            SentimentResult,
        ],
    ] = {}

    analysis_rows: list[
        tuple[
            GeoRunResult,
            dict[
                str,
                SentimentResult,
            ],
        ]
    ] = []

    for result in results:
        task_id = result.task.task_id

        mention = (
            mention_batch.details.get(
                task_id
            )
        )

        if mention is None:
            raise ValueError(
                "missing mention result for task: "
                f"{task_id}"
            )

        task_sentiments: dict[
            str,
            SentimentResult,
        ] = {}

        for target in targets:
            sentiment = await analyze_sentiment(
                result=result,
                mention=mention,
                target=target,
                classifier=classifier,
            )

            task_sentiments[
                target.target_id
            ] = sentiment

        details[
            task_id
        ] = task_sentiments

        analysis_rows.append(
            (
                result,
                task_sentiments,
            )
        )

    return _build_batch_result(
        details=details,
        analysis_rows=analysis_rows,
        targets=targets,
    )


async def analyze_batch_sentiment_with_provider(
        *,
        results: list[GeoRunResult],
        mention_batch: MentionBatchResult,
        targets: list[MentionTarget],
        provider: SentimentModelProvider,
        config: SentimentConfig,
) -> SentimentBatchResult:
    """
    使用正式模型 Provider 执行 Batch Sentiment。

    与轻量 analyze_batch_sentiment 的区别：
    - 使用生产 Provider
    - 支持 retry
    - Context / Prompt / Validation / Rules
      已由 analyze_sentiment_with_provider 负责

    Retry 只针对：
    - rate_limit
    - transient_api_error
    - timeout
    - network_error
    """

    _validate_targets(
        targets
    )

    details: dict[
        str,
        dict[
            str,
            SentimentResult,
        ],
    ] = {}

    analysis_rows: list[
        tuple[
            GeoRunResult,
            dict[
                str,
                SentimentResult,
            ],
        ]
    ] = []

    for result in results:
        task_id = result.task.task_id

        mention = (
            mention_batch.details.get(
                task_id
            )
        )

        if mention is None:
            raise ValueError(
                "missing mention result for task: "
                f"{task_id}"
            )

        task_sentiments: dict[
            str,
            SentimentResult,
        ] = {}

        for target in targets:
            sentiment = (
                await _analyze_sentiment_with_retry(
                    result=result,
                    mention=mention,
                    target=target,
                    provider=provider,
                    config=config,
                )
            )

            task_sentiments[
                target.target_id
            ] = sentiment

        details[
            task_id
        ] = task_sentiments

        analysis_rows.append(
            (
                result,
                task_sentiments,
            )
        )

    return _build_batch_result(
        details=details,
        analysis_rows=analysis_rows,
        targets=targets,
    )


async def _analyze_sentiment_with_retry(
        *,
        result: GeoRunResult,
        mention,
        target: MentionTarget,
        provider: SentimentModelProvider,
        config: SentimentConfig,
) -> SentimentResult:
    """
    单目标生产分析 + 外层 Retry。

    max_retries=2 表示：
        首次请求 + 最多2次重试
        = 最多3次 Provider 请求。
    """

    attempt_count = 0

    accumulated_latencies: list[
        float
    ] = []

    while True:
        attempt_count += 1

        sentiment = (
            await analyze_sentiment_with_provider(
                result=result,
                mention=mention,
                target=target,
                provider=provider,
                config=config,
            )
        )

        if (
                sentiment.status
                == SentimentStatus.NOT_APPLICABLE
        ):
            return sentiment

        for latency in (
                sentiment.request_latencies
        ):
            accumulated_latencies.append(
                latency
            )

        sentiment.attempt_count = (
            attempt_count
        )

        sentiment.request_count = (
            attempt_count
        )

        sentiment.request_latencies = list(
            accumulated_latencies
        )

        if (
                sentiment.error_type
                not in RETRYABLE_SENTIMENT_ERROR_TYPES
        ):
            return sentiment

        retries_used = (
                attempt_count - 1
        )

        if (
                retries_used
                >= config.max_retries
        ):
            return sentiment

        delay_seconds = (
            _retry_delay_seconds(
                config=config,
                retry_index=retries_used,
            )
        )

        if delay_seconds > 0:
            await asyncio.sleep(
                delay_seconds
            )


def _retry_delay_seconds(
        *,
        config: SentimentConfig,
        retry_index: int,
) -> float:
    """
    获取第 N 次 retry 的 backoff。

    例如：
        retry_backoff_seconds=(3, 8)

    第1次 retry -> 3秒
    第2次 retry -> 8秒

    如果 retry 次数超过配置长度，
    后续继续使用最后一个值。
    """

    backoffs = (
        config.retry_backoff_seconds
    )

    if not backoffs:
        return 0.0

    if retry_index < len(
            backoffs
    ):
        return float(
            backoffs[
                retry_index
            ]
        )

    return float(
        backoffs[-1]
    )


def _build_batch_result(
        *,
        details: dict[
            str,
            dict[
                str,
                SentimentResult,
            ],
        ],
        analysis_rows: list[
            tuple[
                GeoRunResult,
                dict[
                    str,
                    SentimentResult,
                ],
            ]
        ],
        targets: list[MentionTarget],
) -> SentimentBatchResult:
    """
    统一构建四套 Sentiment 汇总。
    """

    summaries: dict[
        str,
        TargetSentimentSummary,
    ] = {}

    for target in targets:
        summaries[
            target.target_id
        ] = TargetSentimentSummary(
            target_id=target.target_id,
            target_name=target.name,

            quick=_answer_summary(
                rows=analysis_rows,
                target_id=target.target_id,
                mode=GeoMode.QUICK,
            ),

            expert=_answer_summary(
                rows=analysis_rows,
                target_id=target.target_id,
                mode=GeoMode.EXPERT,
            ),

            all_answers=_answer_summary(
                rows=analysis_rows,
                target_id=target.target_id,
            ),

            question_level=(
                _question_summary(
                    rows=analysis_rows,
                    target_id=(
                        target.target_id
                    ),
                )
            ),
        )

    return SentimentBatchResult(
        details=details,
        summaries=summaries,
    )


def _answer_summary(
        *,
        rows: list[
            tuple[
                GeoRunResult,
                dict[
                    str,
                    SentimentResult,
                ],
            ]
        ],
        target_id: str,
        mode: GeoMode | None = None,
) -> SentimentSummary:
    """
    按回答级汇总情感。

    所有比例分母均为：
        classified_mention_count
    """

    planned_count = 0

    positive_count = 0
    neutral_count = 0
    negative_count = 0

    failed_count = 0

    for result, sentiments in rows:
        if (
                mode is not None
                and result.task.mode != mode
        ):
            continue

        sentiment = sentiments.get(
            target_id
        )

        if sentiment is None:
            continue

        if (
                sentiment.status
                == SentimentStatus.NOT_APPLICABLE
        ):
            continue

        planned_count += 1

        if (
                sentiment.status
                == SentimentStatus.FAILED
        ):
            failed_count += 1
            continue

        if (
                sentiment.status
                not in SUCCESS_STATUSES
        ):
            failed_count += 1
            continue

        label = (
            sentiment.final_sentiment
        )

        if label == SentimentLabel.POSITIVE:
            positive_count += 1

        elif label == SentimentLabel.NEUTRAL:
            neutral_count += 1

        elif label == SentimentLabel.NEGATIVE:
            negative_count += 1

        else:
            failed_count += 1

    return _build_summary(
        planned_count=planned_count,
        positive_count=positive_count,
        neutral_count=neutral_count,
        negative_count=negative_count,
        failed_count=failed_count,
    )


def _question_summary(
        *,
        rows: list[
            tuple[
                GeoRunResult,
                dict[
                    str,
                    SentimentResult,
                ],
            ]
        ],
        target_id: str,
) -> SentimentSummary:
    """
    按 question_id 聚合 Quick / Expert 情感结果。

    豆包既有规则：

    同一个 question + target：

    - 只看成功分类
    - 任一 negative -> negative
    - 否则任一 positive -> positive
    - 否则 -> neutral
    """

    question_results: dict[
        str,
        list[SentimentResult],
    ] = {}

    for result, sentiments in rows:
        sentiment = sentiments.get(
            target_id
        )

        if sentiment is None:
            continue

        if (
                sentiment.status
                == SentimentStatus.NOT_APPLICABLE
        ):
            continue

        question_id = (
            result.task.question_id
        )

        question_results.setdefault(
            question_id,
            [],
        ).append(
            sentiment
        )

    planned_count = len(
        question_results
    )

    positive_count = 0
    neutral_count = 0
    negative_count = 0

    failed_count = 0

    for sentiments in (
            question_results.values()
    ):
        labels = [
            sentiment.final_sentiment
            for sentiment in sentiments
            if (
                    sentiment.status
                    in SUCCESS_STATUSES
                    and sentiment.final_sentiment
                    is not None
            )
        ]

        if not labels:
            failed_count += 1
            continue

        if (
                SentimentLabel.NEGATIVE
                in labels
        ):
            negative_count += 1
            continue

        if (
                SentimentLabel.POSITIVE
                in labels
        ):
            positive_count += 1
            continue

        neutral_count += 1

    return _build_summary(
        planned_count=planned_count,
        positive_count=positive_count,
        neutral_count=neutral_count,
        negative_count=negative_count,
        failed_count=failed_count,
    )


def _build_summary(
        *,
        planned_count: int,
        positive_count: int,
        neutral_count: int,
        negative_count: int,
        failed_count: int,
) -> SentimentSummary:
    classified_count = (
            positive_count
            +
            neutral_count
            +
            negative_count
    )

    non_negative_count = (
            positive_count
            +
            neutral_count
    )

    if classified_count > 0:
        positive_rate = (
                positive_count
                /
                classified_count
        )

        neutral_rate = (
                neutral_count
                /
                classified_count
        )

        negative_rate = (
                negative_count
                /
                classified_count
        )

        non_negative_rate = (
                non_negative_count
                /
                classified_count
        )

    else:
        positive_rate = 0.0
        neutral_rate = 0.0
        negative_rate = 0.0
        non_negative_rate = 0.0

    return SentimentSummary(
        planned_mention_count=(
            planned_count
        ),

        classified_mention_count=(
            classified_count
        ),

        positive_count=positive_count,

        neutral_count=neutral_count,

        negative_count=negative_count,

        non_negative_count=(
            non_negative_count
        ),

        positive_rate=positive_rate,

        neutral_rate=neutral_rate,

        negative_rate=negative_rate,

        non_negative_rate=(
            non_negative_rate
        ),

        classification_failed_count=(
            failed_count
        ),
    )


def _validate_targets(
        targets: list[MentionTarget],
) -> None:
    seen_target_ids: set[str] = set()

    for target in targets:
        target_id = (
            target.target_id.strip()
        )

        if not target_id:
            raise ValueError(
                "target_id cannot be empty"
            )

        if target_id in seen_target_ids:
            raise ValueError(
                "duplicate sentiment target_id: "
                f"{target_id}"
            )

        seen_target_ids.add(
            target_id
        )
