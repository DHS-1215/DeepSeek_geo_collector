from typing import Protocol

from app.analysis.models import (
    MentionResult,
    MentionTarget,
    SentimentLabel,
    SentimentResult,
    SentimentStatus,
)
from app.analysis.sentiment_config import (
    SentimentConfig,
)
from app.analysis.sentiment_context import (
    extract_target_context,
)
from app.analysis.sentiment_prompt import (
    SYSTEM_PROMPT,
    build_user_prompt,
)
from app.analysis.sentiment_providers import (
    SentimentApiError,
    SentimentModelProvider,
)
from app.analysis.sentiment_rules import (
    apply_negative_priority,
    apply_target_specific_overrides,
    finalize_rule_flags,
)
from app.analysis.sentiment_validation import (
    validate_model_payload,
)
from app.core.models import GeoRunResult


class SentimentClassifier(Protocol):
    """
    轻量 Sentiment Classifier 接口。

    主要保留给：
    - 单元测试
    - Fake Classifier
    - 简单规则分类器

    正式生产链路使用 SentimentModelProvider。
    """

    async def classify(
        self,
        *,
        answer_text: str,
        target: MentionTarget,
    ) -> SentimentLabel | str:
        ...


def should_classify_sentiment(
    *,
    result: GeoRunResult,
    mention: MentionResult,
    target_id: str,
) -> bool:
    """
    判断一个目标是否需要执行情感分类。

    与豆包既有口径保持一致：
    - 回答必须有效
    - 回答正文必须非空
    - 当前目标必须被提及
    """

    if not mention.is_valid_answer:
        return False

    if not result.answer_text_clean.strip():
        return False

    target_result = (
        mention.target_results.get(
            target_id
        )
    )

    if target_result is None:
        return False

    return (
        target_result.mention_count
        > 0
    )


async def analyze_sentiment(
    *,
    result: GeoRunResult,
    mention: MentionResult,
    target: MentionTarget,
    classifier: SentimentClassifier,
) -> SentimentResult:
    """
    轻量单条 Sentiment 分析。

    为原有测试和简单 Classifier 保留。
    """

    if not should_classify_sentiment(
        result=result,
        mention=mention,
        target_id=target.target_id,
    ):
        return SentimentResult(
            target_id=target.target_id,
            target_name=target.name,
            status=(
                SentimentStatus
                .NOT_APPLICABLE
            ),
        )

    try:
        raw_label = await classifier.classify(
            answer_text=(
                result.answer_text_clean
            ),
            target=target,
        )

        label = _normalize_label(
            raw_label
        )

    except Exception as exc:
        return SentimentResult(
            target_id=target.target_id,
            target_name=target.name,
            status=SentimentStatus.FAILED,
            reason=str(exc),
            error_type="classifier_error",
            error_message=str(exc),
            provider=(
                _classifier_name(
                    classifier
                )
            ),
        )

    return SentimentResult(
        target_id=target.target_id,
        target_name=target.name,
        status=SentimentStatus.SUCCESS,
        mentioned=True,
        model_sentiment=label,
        final_sentiment=label,
        provider=(
            _classifier_name(
                classifier
            )
        ),
    )


async def analyze_sentiment_with_provider(
    *,
    result: GeoRunResult,
    mention: MentionResult,
    target: MentionTarget,
    provider: SentimentModelProvider,
    config: SentimentConfig,
) -> SentimentResult:
    """
    正式生产级单条 Sentiment Analyzer。

    执行链：

    有效且已提及
        -> Target Context
        -> Prompt
        -> Provider
        -> Payload Validation
        -> model_sentiment
        -> Negative Priority
        -> Target-specific Rules
        -> final_sentiment

    注意：
    本函数只执行“一次” Provider 请求。

    Retry 由 Batch / Orchestration 层负责。
    """

    if not should_classify_sentiment(
        result=result,
        mention=mention,
        target_id=target.target_id,
    ):
        return SentimentResult(
            target_id=target.target_id,
            target_name=target.name,
            status=(
                SentimentStatus
                .NOT_APPLICABLE
            ),
        )

    answer_text = (
        result.answer_text_clean
    )

    target_context = (
        extract_target_context(
            answer_text=answer_text,
            target=target,
            sentences_before=(
                config
                .context_sentences_before
            ),
            sentences_after=(
                config
                .context_sentences_after
            ),
        )
    )

    user_prompt = build_user_prompt(
        target=target,
        target_context=(
            target_context.target_context
        ),
        full_answer=answer_text,
        evidence_max_items=(
            config.evidence_max_items
        ),
    )

    try:
        response = await provider.classify(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

    except SentimentApiError as exc:
        return _provider_error_result(
            target=target,
            provider=provider,
            target_context=target_context,
            error=exc,
        )

    except Exception as exc:
        return SentimentResult(
            target_id=target.target_id,
            target_name=target.name,
            status=SentimentStatus.FAILED,
            mentioned=True,
            matched_aliases=list(
                target_context.matched_aliases
            ),
            target_context=(
                target_context.target_context
            ),
            context_spans=list(
                target_context.context_spans
            ),
            provider=(
                provider.provider_name
            ),
            model_name=(
                provider.model_name
            ),
            prompt_version=(
                config.prompt_version
            ),
            rule_version=(
                config.rule_version
            ),
            error_type="unexpected_error",
            error_message=str(exc),
            reason=str(exc),
            attempt_count=1,
            request_count=1,
        )

    (
        payload,
        validation_error,
        warnings,
        coercion_fields,
        confidence_diagnostics,
    ) = validate_model_payload(
        response.payload,
        target_name=target.name,
        original_answer=answer_text,
        evidence_max_items=(
            config.evidence_max_items
        ),
    )

    if validation_error is not None:
        return SentimentResult(
            target_id=target.target_id,
            target_name=target.name,
            status=SentimentStatus.FAILED,
            mentioned=True,

            matched_aliases=list(
                target_context.matched_aliases
            ),

            target_context=(
                target_context.target_context
            ),

            context_spans=list(
                target_context.context_spans
            ),

            provider=(
                provider.provider_name
            ),

            model_name=(
                provider.model_name
            ),

            prompt_version=(
                config.prompt_version
            ),

            rule_version=(
                config.rule_version
            ),

            warnings=list(warnings),

            schema_coercion_applied=bool(
                coercion_fields
            ),

            schema_coercion_fields=dict(
                coercion_fields
            ),

            confidence_raw=(
                confidence_diagnostics.get(
                    "confidence_raw"
                )
            ),

            confidence_missing=bool(
                confidence_diagnostics.get(
                    "confidence_missing"
                )
            ),

            confidence_fallback_applied=bool(
                confidence_diagnostics.get(
                    "confidence_fallback_applied"
                )
            ),

            error_type="validation_error",

            error_message=(
                validation_error
            ),

            reason=validation_error,

            attempt_count=1,
            request_count=1,

            request_latencies=(
                _response_latencies(
                    response.latency_seconds
                )
            ),

            latency_seconds=(
                response.latency_seconds
            ),

            prompt_tokens=(
                response.prompt_tokens
            ),

            completion_tokens=(
                response.completion_tokens
            ),

            total_tokens=(
                response.total_tokens
            ),

            response_raw_content=(
                response.raw_content
            ),

            response_json_keys=list(
                response.response_json_keys
            ),
        )

    model_sentiment = SentimentLabel(
        str(payload["sentiment"])
    )

    status = (
        SentimentStatus
        .SUCCESS_WITH_WARNINGS
        if warnings
        else SentimentStatus.SUCCESS
    )

    sentiment = SentimentResult(
        target_id=target.target_id,
        target_name=target.name,
        status=status,
        mentioned=True,

        matched_aliases=list(
            target_context.matched_aliases
        ),

        target_context=(
            target_context.target_context
        ),

        context_spans=list(
            target_context.context_spans
        ),

        model_sentiment=(
            model_sentiment
        ),

        final_sentiment=(
            model_sentiment
        ),

        reason=(
            str(payload.get("reason"))
            if payload.get("reason")
            is not None
            else None
        ),

        evidence=list(
            payload.get("evidence")
            or []
        ),

        confidence=(
            payload.get("confidence")
        ),

        provider=(
            provider.provider_name
        ),

        model_name=(
            provider.model_name
        ),

        prompt_version=(
            config.prompt_version
        ),

        rule_version=(
            config.rule_version
        ),

        warnings=list(
            warnings
        ),

        schema_coercion_applied=bool(
            coercion_fields
        ),

        schema_coercion_fields=dict(
            coercion_fields
        ),

        confidence_raw=(
            confidence_diagnostics.get(
                "confidence_raw"
            )
        ),

        confidence_missing=bool(
            confidence_diagnostics.get(
                "confidence_missing"
            )
        ),

        confidence_fallback_applied=bool(
            confidence_diagnostics.get(
                "confidence_fallback_applied"
            )
        ),

        attempt_count=1,

        request_count=1,

        request_latencies=(
            _response_latencies(
                response.latency_seconds
            )
        ),

        latency_seconds=(
            response.latency_seconds
        ),

        prompt_tokens=(
            response.prompt_tokens
        ),

        completion_tokens=(
            response.completion_tokens
        ),

        total_tokens=(
            response.total_tokens
        ),

        response_raw_content=(
            response.raw_content
        ),

        response_json_keys=list(
            response.response_json_keys
        ),
    )

    if config.negative_priority:
        priority_match = (
            apply_negative_priority(
                target_context.target_context,
                target_aliases=(
                    target.aliases
                ),
            )
        )

        if priority_match is not None:
            sentiment.final_sentiment = (
                SentimentLabel.NEGATIVE
            )

            for rule_code in (
                priority_match.get(
                    "rule_codes",
                    [],
                )
            ):
                rule_code = str(
                    rule_code
                )

                if (
                    rule_code
                    not in sentiment
                    .override_rule_codes
                ):
                    sentiment.override_rule_codes.append(
                        rule_code
                    )

            priority_reason = str(
                priority_match.get(
                    "reason"
                )
                or ""
            )

            if priority_reason:
                sentiment.override_reason = (
                    priority_reason
                )

            for evidence in (
                priority_match.get(
                    "evidence",
                    [],
                )
            ):
                _append_rule_evidence(
                    sentiment.evidence,
                    str(evidence),
                    evidence_max_items=(
                        config
                        .evidence_max_items
                    ),
                )

    apply_target_specific_overrides(
        result=sentiment,
        target=target,
        answer_text=answer_text,
        evidence_max_items=(
            config.evidence_max_items
        ),
    )

    finalize_rule_flags(
        sentiment
    )

    return sentiment


def _provider_error_result(
    *,
    target: MentionTarget,
    provider: SentimentModelProvider,
    target_context,
    error: SentimentApiError,
) -> SentimentResult:
    if error.error_type == "rate_limit":
        status = (
            SentimentStatus.RATE_LIMITED
        )

    elif error.error_type == "timeout":
        status = (
            SentimentStatus.TIMEOUT
        )

    else:
        status = SentimentStatus.FAILED

    return SentimentResult(
        target_id=target.target_id,
        target_name=target.name,
        status=status,
        mentioned=True,

        matched_aliases=list(
            target_context.matched_aliases
        ),

        target_context=(
            target_context.target_context
        ),

        context_spans=list(
            target_context.context_spans
        ),

        provider=(
            provider.provider_name
        ),

        model_name=(
            provider.model_name
        ),

        error_type=(
            error.error_type
        ),

        error_code=(
            error.error_code
        ),

        error_message=str(
            error
        ),

        reason=str(
            error
        ),

        attempt_count=1,
        request_count=1,
    )


def _append_rule_evidence(
    evidence: list[str],
    item: str,
    *,
    evidence_max_items: int,
) -> None:
    """
    将规则命中证据加入 evidence。

    语义与豆包规则层保持一致：
    - 不重复
    - max <= 0 时不限制
    - 已满时淘汰最旧一条
    """

    if (
        not item
        or item in evidence
    ):
        return

    if evidence_max_items <= 0:
        evidence.append(
            item
        )
        return

    if (
        len(evidence)
        >= evidence_max_items
    ):
        evidence.pop(0)

    evidence.append(
        item
    )


def _response_latencies(
    latency_seconds: float | None,
) -> list[float]:
    if latency_seconds is None:
        return []

    return [
        latency_seconds
    ]


def _normalize_label(
    value: SentimentLabel | str,
) -> SentimentLabel:
    """
    将轻量分类器输出规范化为标准 SentimentLabel。
    """

    if isinstance(
        value,
        SentimentLabel,
    ):
        return value

    normalized = (
        str(value)
        .strip()
        .lower()
    )

    try:
        return SentimentLabel(
            normalized
        )

    except ValueError as exc:
        raise ValueError(
            "unsupported sentiment label: "
            f"{value!r}"
        ) from exc


def _classifier_name(
    classifier: SentimentClassifier,
) -> str:
    name = getattr(
        classifier,
        "name",
        None,
    )

    if name:
        return str(name)

    return (
        classifier
        .__class__
        .__name__
    )