import asyncio

from app.analysis.mention import (
    analyze_mentions,
)
from app.analysis.models import (
    MentionTarget,
    SentimentLabel,
)
from app.analysis.sentiment import (
    analyze_sentiment_with_provider,
    effective_sentiment_reason,
)
from app.analysis.sentiment_config import (
    load_sentiment_config,
)
from app.analysis.sentiment_providers import (
    create_sentiment_provider,
)
from app.core.enums import (
    GeoMode,
    TaskStatus,
    ValidationStatus,
)
from app.core.models import (
    GeoRunResult,
    GeoTask,
    ValidationResult,
)

TARGET = MentionTarget(
    target_id="hongmao_yaojiu",
    name="鸿茅药酒",
    aliases=[
        "鸿茅药酒",
    ],
)

CASES = [
    {
        "name": "neutral_fact",
        "answer": (
            "鸿茅药酒属于正规药品，"
            "具有批准文号和生产企业信息。"
        ),
        "expected": SentimentLabel.NEUTRAL,
    },
    {
        "name": "positive_recommendation",
        "answer": (
            "鸿茅药酒整体值得推荐，"
            "产品可靠，也值得消费者选择。"
        ),
        "expected": SentimentLabel.POSITIVE,
    },
    {
        "name": "discourage_purchase",
        "answer": (
            "综合考虑后，鸿茅药酒不建议购买。"
        ),
        "expected": SentimentLabel.NEGATIVE,
    },
    {
        "name": "negated_false_advertising",
        "answer": (
            "目前没有证据表明鸿茅药酒存在虚假宣传问题。"
        ),
        "expected": SentimentLabel.NEUTRAL,
    },
    {
        "name": "tan_qindong",
        "answer": (
            "关于鸿茅药酒的相关讨论中提到了谭秦东。"
        ),
        "expected": SentimentLabel.NEGATIVE,
    },
    {
        "name": "cross_province",
        "answer": (
            "鸿茅药酒相关事件中曾出现跨省这一关键词。"
        ),
        "expected": SentimentLabel.NEGATIVE,
    },
    {
        "name": "false_advertising",
        "answer": (
            "鸿茅药酒曾被指出存在虚假宣传问题。"
        ),
        "expected": SentimentLabel.NEGATIVE,
    },
]


def build_result(
        *,
        index: int,
        answer: str,
) -> GeoRunResult:
    return GeoRunResult(
        provider="deepseek",

        run_id=(
            f"sentiment_smoke_{index}"
        ),

        task=GeoTask(
            task_id=(
                f"SMOKE_{index:02d}_quick"
            ),
            question_id=(
                f"SMOKE_{index:02d}"
            ),
            question="Sentiment Smoke Test",
            mode=GeoMode.QUICK,
        ),

        answer_text_raw=answer,

        answer_text_clean=answer,

        validation=ValidationResult(
            status=ValidationStatus.PASS,
            is_complete=True,
        ),

        status=TaskStatus.SUCCESS,
    )


async def main() -> None:
    config = load_sentiment_config()

    provider = create_sentiment_provider(
        config
    )

    print("=" * 72)
    print("DeepSeek GEO Sentiment Ollama Smoke")
    print("=" * 72)

    print(
        f"provider      : {provider.provider_name}"
    )
    print(
        f"model         : {provider.model_name}"
    )
    print(
        f"prompt_version: {config.prompt_version}"
    )
    print(
        f"rule_version  : {config.rule_version}"
    )

    healthy = await provider.health_check()

    print(
        f"health_check  : {healthy}"
    )

    if not healthy:
        raise SystemExit(
            "Ollama health check failed."
        )

    print()

    passed = 0

    for index, case in enumerate(
            CASES,
            start=1,
    ):
        result = build_result(
            index=index,
            answer=case["answer"],
        )

        mention = analyze_mentions(
            result=result,
            targets=[
                TARGET
            ],
        )

        sentiment = (
            await analyze_sentiment_with_provider(
                result=result,
                mention=mention,
                target=TARGET,
                provider=provider,
                config=config,
            )
        )

        actual = (
            sentiment.final_sentiment
        )

        expected = case["expected"]

        ok = actual == expected

        if ok:
            passed += 1

        print(
            f"[{'PASS' if ok else 'FAIL'}] "
            f"{case['name']}"
        )

        print(
            f"  status            = "
            f"{sentiment.status.value}"
        )

        model_sentiment_value = (
            sentiment.model_sentiment.value
            if sentiment.model_sentiment
            else None
        )

        final_sentiment_value = (
            sentiment.final_sentiment.value
            if sentiment.final_sentiment
            else None
        )

        print(
            f"  model_sentiment   = {model_sentiment_value}"
        )

        print(
            f"  final_sentiment   = {final_sentiment_value}"
        )

        print(
            f"  expected          = "
            f"{expected.value}"
        )

        print(
            f"  confidence        = "
            f"{sentiment.confidence}"
        )

        print(
            f"  rule_hit          = "
            f"{sentiment.rule_hit}"
        )

        print(
            f"  rule_override     = "
            f"{sentiment.rule_override}"
        )

        print(
            f"  override_codes    = "
            f"{sentiment.override_rule_codes}"
        )

        print(
            f"  model_reason      = "
            f"{sentiment.reason}"
        )

        print(
            f"  override_reason   = "
            f"{sentiment.override_reason}"
        )

        print(
            f"  effective_reason  = "
            f"{effective_sentiment_reason(sentiment)}"
        )

        print(
            f"  evidence          = "
            f"{sentiment.evidence}"
        )

        print(
            f"  warnings          = "
            f"{sentiment.warnings}"
        )

        print(
            f"  latency_seconds   = "
            f"{sentiment.latency_seconds}"
        )

        print()

    print("=" * 72)

    print(
        f"RESULT: {passed}/{len(CASES)} passed"
    )

    if passed != len(CASES):
        raise SystemExit(1)

    print("SMOKE PASS")


if __name__ == "__main__":
    asyncio.run(
        main()
    )
