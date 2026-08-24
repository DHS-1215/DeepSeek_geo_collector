from app.analysis.mention import (
    analyze_mentions,
    analyze_target,
    is_valid_analysis_answer,
    normalize_text,
)
from app.analysis.models import (
    MentionTarget,
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


def _build_result(
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
        question=(
            "这个产品怎么样？"
        ),
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


def _hongmao_target() -> MentionTarget:
    return MentionTarget(
        target_id="hongmao_yaojiu",
        name="鸿茅药酒",
        aliases=[
            "鸿茅药酒",
        ],
    )


def test_normalize_text() -> None:
    assert normalize_text(
        "  ABC\u3000鸿茅药酒  "
    ) == "abc 鸿茅药酒"


def test_valid_answer() -> None:
    result = _build_result(
        answer="正常回答"
    )

    assert (
            is_valid_analysis_answer(
                result
            )
            is True
    )


def test_pass_with_warnings_is_valid() -> None:
    result = _build_result(
        answer="正常回答",
        validation_status=(
            ValidationStatus
            .PASS_WITH_WARNINGS
        ),
    )

    assert (
            is_valid_analysis_answer(
                result
            )
            is True
    )


def test_failed_task_is_not_valid() -> None:
    result = _build_result(
        answer="鸿茅药酒",
        status=TaskStatus.FAILED,
    )

    assert (
            is_valid_analysis_answer(
                result
            )
            is False
    )


def test_validation_fail_is_not_valid() -> None:
    result = _build_result(
        answer="鸿茅药酒",
        validation_status=(
            ValidationStatus.FAIL
        ),
    )

    assert (
            is_valid_analysis_answer(
                result
            )
            is False
    )


def test_empty_answer_is_not_valid() -> None:
    result = _build_result(
        answer="   "
    )

    assert (
            is_valid_analysis_answer(
                result
            )
            is False
    )


def test_target_detects_single_mention() -> None:
    result = analyze_target(
        answer_text=(
            "鸿茅药酒属于药品。"
        ),
        target=_hongmao_target(),
    )

    assert result.mention_count == 1

    assert result.matched_terms == [
        "鸿茅药酒"
    ]


def test_target_counts_multiple_mentions() -> None:
    result = analyze_target(
        answer_text=(
            "鸿茅药酒是一种药品，"
            "使用鸿茅药酒前应阅读说明书。"
        ),
        target=_hongmao_target(),
    )

    assert result.mention_count == 2


def test_alias_allows_whitespace_between_chars() -> None:
    result = analyze_target(
        answer_text=(
            "鸿 茅 药 酒属于药品。"
        ),
        target=_hongmao_target(),
    )

    assert result.mention_count == 1


def test_target_supports_aliases() -> None:
    target = MentionTarget(
        target_id="test_product",
        name="测试产品",
        aliases=[
            "测试产品",
            "测试牌产品",
        ],
    )

    result = analyze_target(
        answer_text=(
            "这里提到了测试牌产品。"
        ),
        target=target,
    )

    assert result.mention_count == 1

    assert result.matched_terms == [
        "测试牌产品"
    ]


def test_analyze_mentions_detects_target() -> None:
    result = _build_result(
        answer=(
            "鸿茅药酒是正规药品。"
        )
    )

    mention = analyze_mentions(
        result=result,
        targets=[
            _hongmao_target()
        ],
    )

    assert mention.is_valid_answer is True

    assert mention.mention_any is True

    assert mention.mentioned_target_ids == [
        "hongmao_yaojiu"
    ]

    assert (
            mention.target_results[
                "hongmao_yaojiu"
            ].mention_count
            == 1
    )


def test_analyze_mentions_without_target() -> None:
    result = _build_result(
        answer=(
            "这是一段普通回答。"
        )
    )

    mention = analyze_mentions(
        result=result,
        targets=[
            _hongmao_target()
        ],
    )

    assert mention.is_valid_answer is True

    assert mention.mention_any is False

    assert mention.mentioned_target_ids == []


def test_invalid_answer_never_counts_mention() -> None:
    result = _build_result(
        answer="鸿茅药酒",
        validation_status=(
            ValidationStatus.FAIL
        ),
    )

    mention = analyze_mentions(
        result=result,
        targets=[
            _hongmao_target()
        ],
    )

    assert mention.is_valid_answer is False

    assert mention.mention_any is False

    assert mention.mentioned_target_ids == []


def test_question_text_does_not_count_as_mention() -> None:
    task = GeoTask(
        task_id="Q001_quick",
        question_id="Q001",
        question=(
            "鸿茅药酒是什么？"
        ),
        mode=GeoMode.QUICK,
    )

    result = GeoRunResult(
        provider="deepseek",
        run_id="run_test",
        task=task,

        answer_text_raw=(
            "这是一个没有品牌名称的回答。"
        ),

        answer_text_clean=(
            "这是一个没有品牌名称的回答。"
        ),

        validation=ValidationResult(
            status=ValidationStatus.PASS,
            is_complete=True,
        ),

        status=TaskStatus.SUCCESS,
    )

    mention = analyze_mentions(
        result=result,
        targets=[
            _hongmao_target()
        ],
    )

    assert mention.mention_any is False
