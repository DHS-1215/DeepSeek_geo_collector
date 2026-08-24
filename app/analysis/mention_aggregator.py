from app.analysis.mention import (
    analyze_mentions,
)
from app.analysis.models import (
    MentionBatchResult,
    MentionResult,
    MentionSummary,
    MentionTarget,
    TargetMentionSummary,
)
from app.core.enums import GeoMode
from app.core.models import GeoRunResult


def analyze_batch_mentions(
        *,
        results: list[GeoRunResult],
        targets: list[MentionTarget],
) -> MentionBatchResult:
    """
    对一个 Batch 的采集结果执行提及分析并生成汇总。

    输出保持豆包 GEO 的四套口径：
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
        MentionResult,
    ] = {}

    analysis_rows: list[
        tuple[
            GeoRunResult,
            MentionResult,
        ]
    ] = []

    for result in results:
        mention_result = analyze_mentions(
            result=result,
            targets=targets,
        )

        details[
            result.task.task_id
        ] = mention_result

        analysis_rows.append(
            (
                result,
                mention_result,
            )
        )

    summaries: dict[
        str,
        TargetMentionSummary,
    ] = {}

    for target in targets:
        summaries[
            target.target_id
        ] = TargetMentionSummary(
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

            question_level=_question_summary(
                rows=analysis_rows,
                target_id=target.target_id,
            ),
        )

    return MentionBatchResult(
        details=details,
        summaries=summaries,
    )


def _answer_summary(
        *,
        rows: list[
            tuple[
                GeoRunResult,
                MentionResult,
            ]
        ],
        target_id: str,
        mode: GeoMode | None = None,
) -> MentionSummary:
    """
    按回答级计算提及率。

    mention_rate =
        mentioned_count
        /
        valid_count
    """

    valid_count = 0
    mentioned_count = 0

    for result, mention in rows:
        if (
                mode is not None
                and result.task.mode != mode
        ):
            continue

        if not mention.is_valid_answer:
            continue

        valid_count += 1

        if _mentions_target(
                mention,
                target_id,
        ):
            mentioned_count += 1

    return _build_summary(
        valid_count=valid_count,
        mentioned_count=(
            mentioned_count
        ),
    )


def _question_summary(
        *,
        rows: list[
            tuple[
                GeoRunResult,
                MentionResult,
            ]
        ],
        target_id: str,
) -> MentionSummary:
    """
    按 question_id 聚合 Quick / Expert。

    一个问题：
    - 至少存在一个有效回答 -> 进入分母
    - 至少一个有效回答提及目标 -> 进入分子
    """

    question_states: dict[
        str,
        bool,
    ] = {}

    for result, mention in rows:
        if not mention.is_valid_answer:
            continue

        question_id = (
            result.task.question_id
        )

        mentioned = _mentions_target(
            mention,
            target_id,
        )

        previous = question_states.get(
            question_id,
            False,
        )

        question_states[
            question_id
        ] = (
                previous
                or mentioned
        )

    valid_count = len(
        question_states
    )

    mentioned_count = sum(
        1
        for mentioned
        in question_states.values()
        if mentioned
    )

    return _build_summary(
        valid_count=valid_count,
        mentioned_count=(
            mentioned_count
        ),
    )


def _mentions_target(
        mention: MentionResult,
        target_id: str,
) -> bool:
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


def _build_summary(
        *,
        valid_count: int,
        mentioned_count: int,
) -> MentionSummary:
    mention_rate = (
        mentioned_count
        / valid_count
        if valid_count > 0
        else 0.0
    )

    return MentionSummary(
        valid_count=valid_count,
        mentioned_count=(
            mentioned_count
        ),
        mention_rate=mention_rate,
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
                "duplicate mention target_id: "
                f"{target_id}"
            )

        seen_target_ids.add(
            target_id
        )
