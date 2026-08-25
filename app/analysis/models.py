from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SentimentLabel(str, Enum):
    """
    品牌情感分类结果。

    与豆包 GEO 系统保持一致，只允许三种业务情感。
    """

    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class SentimentStatus(str, Enum):
    """
    单条情感分析执行状态。
    与豆包 GEO Sentiment 状态语义保持一致。
    """

    SUCCESS = "success"
    SUCCESS_WITH_WARNINGS = (
        "success_with_warnings"
    )

    FAILED = "failed"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    NOT_APPLICABLE = "not_applicable"


@dataclass(slots=True)
class MentionTarget:
    """
    GEO 提及分析目标。

    aliases 中保存该目标允许识别的名称和别名。
    """

    target_id: str

    name: str

    aliases: list[str] = field(
        default_factory=list
    )


@dataclass(slots=True)
class TargetMentionResult:
    """
    单个目标品牌在一条回答中的提及结果。
    """

    target_id: str

    mention_count: int = 0

    matched_terms: list[str] = field(
        default_factory=list
    )


@dataclass(slots=True)
class MentionResult:
    """
    一条回答的品牌提及分析结果。
    """

    is_valid_answer: bool

    mention_any: bool = False

    mentioned_target_ids: list[str] = field(
        default_factory=list
    )

    target_results: dict[
        str,
        TargetMentionResult,
    ] = field(
        default_factory=dict
    )


@dataclass(slots=True)
class TargetContext:
    """
    Sentiment 分析使用的目标上下文。

    matched_aliases:
        实际命中的目标名称/别名。

    context_spans:
        alias 在原始回答中的位置及所在句。
    """

    target_context: str = ""

    matched_aliases: list[str] = field(
        default_factory=list
    )

    context_spans: list[
        dict[str, int | str]
    ] = field(
        default_factory=list
    )


@dataclass(slots=True)
class ModelResponse:
    """
    Sentiment Provider 的一次模型响应。

    Provider 负责单次请求；
    Retry 由上层 orchestration 负责。
    """

    payload: dict[
        str,
        Any,
    ] = field(
        default_factory=dict
    )

    latency_seconds: float | None = None

    prompt_tokens: int | None = None

    completion_tokens: int | None = None

    total_tokens: int | None = None

    raw_content: str | None = None

    response_json_keys: list[str] = field(
        default_factory=list
    )

    request_started_at: str | None = None

    request_finished_at: str | None = None


@dataclass(slots=True)
class SentimentResult:
    """
    一个目标品牌在一条回答中的完整情感分析结果。

    model_sentiment:
        模型原始分类结果。

    final_sentiment:
        经过业务规则修正后的最终分类结果。

    GEO 中正率必须使用 final_sentiment。
    """

    target_id: str

    status: SentimentStatus

    target_name: str | None = None

    mentioned: bool = False

    matched_aliases: list[str] = field(
        default_factory=list
    )

    target_context: str = ""

    context_spans: list[
        dict[str, int | str]
    ] = field(
        default_factory=list
    )

    model_sentiment: (
            SentimentLabel | None
    ) = None

    final_sentiment: (
            SentimentLabel | None
    ) = None

    reason: str | None = None

    evidence: list[str] = field(
        default_factory=list
    )

    confidence: float | None = None

    provider: str | None = None

    model_name: str | None = None

    prompt_version: str | None = None

    rule_version: str | None = None

    override_rule_codes: list[str] = field(
        default_factory=list
    )

    override_reason: str | None = None

    rule_hit: bool = False

    rule_override: bool = False

    override_applied: bool = False

    suppressed_rule_candidates: list[
        dict[str, Any]
    ] = field(
        default_factory=list
    )

    warnings: list[str] = field(
        default_factory=list
    )

    schema_coercion_applied: bool = False

    schema_coercion_fields: dict[
        str,
        str,
    ] = field(
        default_factory=dict
    )

    confidence_raw: Any = None

    confidence_missing: bool = False

    confidence_fallback_applied: bool = False

    error_type: str | None = None

    error_code: str | None = None

    error_message: str | None = None

    attempt_count: int = 0

    request_count: int = 0

    request_latencies: list[float] = field(
        default_factory=list
    )

    retried: bool = False

    latency_seconds: float | None = None

    prompt_tokens: int | None = None

    completion_tokens: int | None = None

    total_tokens: int | None = None

    response_raw_content: str | None = None

    response_json_keys: list[str] = field(
        default_factory=list
    )


@dataclass(slots=True)
class SourceRankItem:
    """
    Source TopN 中的单个标准信源。
    """

    source_key: str

    occurrence_count: int

    question_count: int

    average_order: float

    first_seen_order: int

    share: float

    title: str | None = None

    site_name: str | None = None

    canonical_url: str | None = None


@dataclass(slots=True)
class SourceTop10Summary:
    """
    一批回答的 Source Top10 聚合结果。

    信源率沿用豆包业务口径：

    top10_share =
        top10_occurrences
        /
        total_occurrences
    """

    total_occurrences: int = 0

    top10_occurrences: int = 0

    top10_share: float = 0.0

    outside_top10_occurrences: int = 0

    outside_top10_share: float = 0.0

    items: list[SourceRankItem] = field(
        default_factory=list
    )


@dataclass(slots=True)
class MentionSummary:
    """
    提及率汇总结果。
    """

    valid_count: int = 0

    mentioned_count: int = 0

    mention_rate: float = 0.0


@dataclass(slots=True)
class TargetMentionSummary:
    """
    单个分析目标的提及率汇总。

    同时保留：
    - Quick
    - Expert
    - 全部回答
    - 问题级
    四套豆包既有业务口径。
    """

    target_id: str
    target_name: str

    quick: MentionSummary = field(
        default_factory=MentionSummary
    )

    expert: MentionSummary = field(
        default_factory=MentionSummary
    )

    all_answers: MentionSummary = field(
        default_factory=MentionSummary
    )

    question_level: MentionSummary = field(
        default_factory=MentionSummary
    )


@dataclass(slots=True)
class MentionBatchResult:
    """
    一个 Batch 的完整 Mention Analysis 结果。

    details：
        task_id -> 单条回答 MentionResult

    summaries：
        target_id -> TargetMentionSummary
    """

    details: dict[
        str,
        MentionResult,
    ] = field(
        default_factory=dict
    )

    summaries: dict[
        str,
        TargetMentionSummary,
    ] = field(
        default_factory=dict
    )


@dataclass(slots=True)
class SentimentSummary:
    """
    情感及中正率汇总结果。
    """

    planned_mention_count: int = 0

    classified_mention_count: int = 0

    positive_count: int = 0

    neutral_count: int = 0

    negative_count: int = 0

    non_negative_count: int = 0

    positive_rate: float = 0.0

    neutral_rate: float = 0.0

    negative_rate: float = 0.0

    non_negative_rate: float = 0.0

    classification_failed_count: int = 0


@dataclass(slots=True)
class TargetSentimentSummary:
    """
    单个目标品牌的情感汇总。

    保留豆包既有四套统计口径。
    """

    target_id: str
    target_name: str

    quick: SentimentSummary = field(
        default_factory=SentimentSummary
    )

    expert: SentimentSummary = field(
        default_factory=SentimentSummary
    )

    all_answers: SentimentSummary = field(
        default_factory=SentimentSummary
    )

    question_level: SentimentSummary = field(
        default_factory=SentimentSummary
    )


@dataclass(slots=True)
class SentimentBatchResult:
    """
    一个 Batch 的完整 Sentiment Analysis 结果。

    details:
        task_id
        -> target_id
        -> SentimentResult

    summaries:
        target_id
        -> TargetSentimentSummary
    """

    details: dict[
        str,
        dict[
            str,
            SentimentResult,
        ],
    ] = field(
        default_factory=dict
    )

    summaries: dict[
        str,
        TargetSentimentSummary,
    ] = field(
        default_factory=dict
    )


@dataclass(slots=True)
class BatchAnalysisSummary:
    """
    一个 Batch 的核心 GEO Analysis 汇总。
    """

    mention: MentionSummary = field(
        default_factory=MentionSummary
    )

    sentiment: SentimentSummary = field(
        default_factory=SentimentSummary
    )

    sources: SourceTop10Summary = field(
        default_factory=SourceTop10Summary
    )
