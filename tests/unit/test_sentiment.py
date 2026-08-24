import asyncio

from app.analysis.mention import (
    analyze_mentions,
)
from app.analysis.models import (
    MentionTarget,
    SentimentLabel,
    SentimentStatus,
)
from app.analysis.sentiment import (
    analyze_sentiment,
    should_classify_sentiment,
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


class FakeClassifier:
    name = "fake-classifier"

    def __init__(
            self,
            result: SentimentLabel | str,
    ) -> None:
        self.result = result
        self.call_count = 0

    async def classify(
            self,
            *,
            answer_text: str,
            target: MentionTarget,
    ) -> SentimentLabel | str:
        self.call_count += 1
        return self.result


class FailingClassifier:
    name = "failing-classifier"

    async def classify(
            self,
            *,
            answer_text: str,
            target: MentionTarget,
    ) -> SentimentLabel:
        raise RuntimeError(
            "classifier failed"
        )


def _target() -> MentionTarget:
    return MentionTarget(
        target_id="hongmao_yaojiu",
        name="鸿茅药酒",
        aliases=[
            "鸿茅药酒",
        ],
    )


def _result(
        *,
        answer: str,
        status: TaskStatus = TaskStatus.SUCCESS,
        validation_status: (
                ValidationStatus
        ) = ValidationStatus.PASS,
) -> GeoRunResult:
    task = GeoTask(
        task_id="Q001_quick",
        question_id="Q001",
        question="测试问题",
        mode=GeoMode.QUICK,
    )

    return GeoRunResult(
        provider="deepseek",
        run_id="run_test",
        task=task,
        answer_text_raw=answer,
        answer_text_clean=answer,
        validation=ValidationResult(
            status=validation_status,
            is_complete=True,
        ),
        status=status,
    )


def test_should_classify_when_target_mentioned() -> None:
    result = _result(
        answer="鸿茅药酒是正规药品。"
    )

    mention = analyze_mentions(
        result=result,
        targets=[_target()],
    )

    assert (
            should_classify_sentiment(
                result=result,
                mention=mention,
                target_id="hongmao_yaojiu",
            )
            is True
    )


def test_should_not_classify_without_mention() -> None:
    result = _result(
        answer="这是普通回答。"
    )

    mention = analyze_mentions(
        result=result,
        targets=[_target()],
    )

    assert (
            should_classify_sentiment(
                result=result,
                mention=mention,
                target_id="hongmao_yaojiu",
            )
            is False
    )


def test_should_not_classify_invalid_answer() -> None:
    result = _result(
        answer="鸿茅药酒。",
        validation_status=(
            ValidationStatus.FAIL
        ),
    )

    mention = analyze_mentions(
        result=result,
        targets=[_target()],
    )

    assert (
            should_classify_sentiment(
                result=result,
                mention=mention,
                target_id="hongmao_yaojiu",
            )
            is False
    )


def test_positive_sentiment() -> None:
    result = _result(
        answer="鸿茅药酒整体表现不错。"
    )

    mention = analyze_mentions(
        result=result,
        targets=[_target()],
    )

    classifier = FakeClassifier(
        SentimentLabel.POSITIVE
    )

    sentiment = asyncio.run(
        analyze_sentiment(
            result=result,
            mention=mention,
            target=_target(),
            classifier=classifier,
        )
    )

    assert (
            sentiment.status
            == SentimentStatus.SUCCESS
    )

    assert (
            sentiment.final_sentiment
            == SentimentLabel.POSITIVE
    )

    assert (
            sentiment.provider
            == "fake-classifier"
    )

    assert classifier.call_count == 1


def test_neutral_sentiment_from_string() -> None:
    result = _result(
        answer="鸿茅药酒属于一种药品。"
    )

    mention = analyze_mentions(
        result=result,
        targets=[_target()],
    )

    classifier = FakeClassifier(
        "neutral"
    )

    sentiment = asyncio.run(
        analyze_sentiment(
            result=result,
            mention=mention,
            target=_target(),
            classifier=classifier,
        )
    )

    assert (
            sentiment.final_sentiment
            == SentimentLabel.NEUTRAL
    )


def test_negative_sentiment() -> None:
    result = _result(
        answer="鸿茅药酒存在明显负面评价。"
    )

    mention = analyze_mentions(
        result=result,
        targets=[_target()],
    )

    classifier = FakeClassifier(
        SentimentLabel.NEGATIVE
    )

    sentiment = asyncio.run(
        analyze_sentiment(
            result=result,
            mention=mention,
            target=_target(),
            classifier=classifier,
        )
    )

    assert (
            sentiment.final_sentiment
            == SentimentLabel.NEGATIVE
    )


def test_not_mentioned_returns_not_applicable() -> None:
    result = _result(
        answer="这是普通回答。"
    )

    mention = analyze_mentions(
        result=result,
        targets=[_target()],
    )

    classifier = FakeClassifier(
        SentimentLabel.POSITIVE
    )

    sentiment = asyncio.run(
        analyze_sentiment(
            result=result,
            mention=mention,
            target=_target(),
            classifier=classifier,
        )
    )

    assert (
            sentiment.status
            == SentimentStatus.NOT_APPLICABLE
    )

    assert sentiment.final_sentiment is None

    assert classifier.call_count == 0


def test_invalid_answer_returns_not_applicable() -> None:
    result = _result(
        answer="鸿茅药酒。",
        validation_status=(
            ValidationStatus.FAIL
        ),
    )

    mention = analyze_mentions(
        result=result,
        targets=[_target()],
    )

    classifier = FakeClassifier(
        SentimentLabel.POSITIVE
    )

    sentiment = asyncio.run(
        analyze_sentiment(
            result=result,
            mention=mention,
            target=_target(),
            classifier=classifier,
        )
    )

    assert (
            sentiment.status
            == SentimentStatus.NOT_APPLICABLE
    )

    assert classifier.call_count == 0


def test_classifier_failure_returns_failed() -> None:
    result = _result(
        answer="鸿茅药酒是药品。"
    )

    mention = analyze_mentions(
        result=result,
        targets=[_target()],
    )

    sentiment = asyncio.run(
        analyze_sentiment(
            result=result,
            mention=mention,
            target=_target(),
            classifier=(
                FailingClassifier()
            ),
        )
    )

    assert (
            sentiment.status
            == SentimentStatus.FAILED
    )

    assert sentiment.final_sentiment is None

    assert (
            sentiment.reason
            == "classifier failed"
    )


def test_invalid_classifier_label_returns_failed() -> None:
    result = _result(
        answer="鸿茅药酒是药品。"
    )

    mention = analyze_mentions(
        result=result,
        targets=[_target()],
    )

    classifier = FakeClassifier(
        "unknown"
    )

    sentiment = asyncio.run(
        analyze_sentiment(
            result=result,
            mention=mention,
            target=_target(),
            classifier=classifier,
        )
    )

    assert (
            sentiment.status
            == SentimentStatus.FAILED
    )

    assert sentiment.final_sentiment is None

    assert (
            "unsupported sentiment label"
            in (
                    sentiment.reason
                    or ""
            )
    )