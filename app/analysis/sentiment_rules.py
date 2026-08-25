import re
from typing import Any

from app.analysis.models import (
    MentionTarget,
    SentimentLabel,
    SentimentResult,
)


NEG_TAN_QINDONG_RULE_CODE = (
    "NEG_TAN_QINDONG_MENTION"
)
TAN_QINDONG_KEYWORD = "谭秦东"
TAN_QINDONG_OVERRIDE_REASON = (
    "鸿茅药酒正文中出现业务指定负面人物关键词：谭秦东"
)

NEG_CROSS_PROVINCE_RULE_CODE = (
    "NEG_CROSS_PROVINCE_MENTION"
)
CROSS_PROVINCE_KEYWORD = "跨省"
CROSS_PROVINCE_OVERRIDE_REASON = (
    "鸿茅药酒正文中出现业务指定负面关键词：跨省"
)


NEGATION_PREFIXES = [
    "没有证据表明",
    "无证据表明",
    "不能证明",
    "并未被",
    "未被",
    "未要求",
    "未收到",
    "未发现",
    "暂无",
    "不存在",
    "并无",
    "没有",
    "无",
    "未",
    "不",
]


NEGATIVE_RULES = {
    "NEG_DISCOURAGE_PURCHASE": [
        "不建议购买",
        "不建议盲目购买",
        "不建议使用",
        "不推荐购买",
        "不推荐使用",
        "不值得购买",
        "不值得使用",
        "明确劝退",
    ],
    "NEG_ADVERTISING_CONTROVERSY": [
        "存在广告宣传争议",
        "曾存在广告宣传争议",
        "广告宣传争议",
    ],
    "NEG_FALSE_ADVERTISING": [
        "涉嫌虚假宣传",
        "违规宣传",
    ],
    "NEG_REGULATORY_PENALTY": [
        "被监管处罚",
        "曾被监管处罚",
        "撤销批准",
    ],
    "NEG_QUALITY_PROBLEM": [
        "产品质量存在问题",
        "产品质量存在严重问题",
        "产品本身存在质量问题",
        "产品本身存在明显质量问题",
        "产品存在明显质量问题",
        "该产品存在严重质量问题",
        "产品存在严重质量问题",
    ],
    "NEG_HIGH_RISK": [
        "产品本身存在较高安全风险",
        "该产品本身存在较高安全风险",
        "产品本身存在明显安全风险",
        "该产品本身存在明显安全风险",
        "产品本身安全风险较高",
        "该产品本身安全风险较高",
        "产品本身存在严重隐患",
    ],
    "NEG_EFFICACY_DOUBT": [
        "疗效证据不足",
        "疗效存疑",
    ],
    "NEG_UNRELIABLE_PRODUCT": [
        "产品不可靠",
        "产品不正规",
        "该产品不可靠",
        "该产品不正规",
        "产品本身不可靠",
        "产品本身不正规",
    ],
}


TARGET_SPECIFIC_NEGATIVE_RULES = [
    {
        "target_id": "hongmao_yaojiu",
        "keyword": TAN_QINDONG_KEYWORD,
        "rule_code": (
            NEG_TAN_QINDONG_RULE_CODE
        ),
        "reason": (
            TAN_QINDONG_OVERRIDE_REASON
        ),
    },
    {
        "target_id": "hongmao_yaojiu",
        "keyword": CROSS_PROVINCE_KEYWORD,
        "rule_code": (
            NEG_CROSS_PROVINCE_RULE_CODE
        ),
        "reason": (
            CROSS_PROVINCE_OVERRIDE_REASON
        ),
    },
]


HONGMAO_FULL_ANSWER_NEGATIVE_FACT_RULES = {
    "NEG_HONGMAO_FALSE_ADVERTISING": [
        "虚假宣传",
    ],
    "NEG_HONGMAO_EXAGGERATED_CLAIMS": [
        "夸大宣传",
        "夸大疗效",
        "夸大功效",
        "发布夸大、违规广告",
        "发布夸大违规广告",
    ],
    "NEG_HONGMAO_ADVERTISING_VIOLATION": [
        "广告违规",
        "违法广告",
        "违规广告",
        "广告内容违规",
    ],
    "NEG_HONGMAO_OFF_LABEL_PROMOTION": [
        "超出说明书范围宣传",
        "广告超出说明书范围",
        "超出说明书范围",
    ],
    "NEG_HONGMAO_WEAKENED_DRUG_IDENTITY": [
        "模糊或弱化药品身份",
        "模糊药品身份",
        "弱化药品身份",
    ],
    "NEG_HONGMAO_REGULATORY_NOTICE": [
        "被监管部门通报",
        "监管部门通报",
        "被多地监管部门通报",
        "多地监管部门通报",
    ],
    "NEG_HONGMAO_REGULATORY_PENALTY": [
        "被监管部门处罚",
        "监管部门处罚",
        "监管部门通报处罚",
        "多地监管部门通报处罚",
    ],
    "NEG_HONGMAO_SALES_SUSPENSION": [
        "暂停销售",
    ],
    "NEG_HONGMAO_RECTIFICATION_REQUIRED": [
        "被要求限期整改",
        "要求限期整改",
        "被监管部门要求整改",
        "曾被监管部门要求整改",
        "被责令整改",
        "责令整改",
        "被要求整改",
        "要求整改",
        "正在整改",
        "整改尚未完成",
        "收到整改通知",
        "存在整改要求",
        "整改要求",
    ],
}


def apply_negative_priority(
    target_context: str,
    *,
    target_aliases: list[str] | None = None,
) -> dict[str, Any] | None:
    matched_codes: list[str] = []
    matched_evidence: list[str] = []

    scan_texts = _target_relevant_sentences(
        target_context,
        target_aliases,
    )

    for code, phrases in (
        NEGATIVE_RULES.items()
    ):
        for phrase in phrases:
            if any(
                _phrase_has_unnegated_match(
                    text,
                    phrase,
                )
                for text in scan_texts
            ):
                matched_codes.append(code)
                matched_evidence.append(
                    phrase
                )
                break

    if not matched_codes:
        return None

    return {
        "rule_codes": matched_codes,
        "reason": (
            "目标上下文明确否定产品本身或包含明确劝退结论，"
            "按负面优先规则判为 negative。"
        ),
        "evidence": matched_evidence,
    }


def apply_target_specific_overrides(
    *,
    result: SentimentResult,
    target: MentionTarget,
    answer_text: str,
    evidence_max_items: int,
) -> None:
    matched_reasons: list[str] = []

    for rule in (
        TARGET_SPECIFIC_NEGATIVE_RULES
    ):
        if (
            target.target_id
            != rule["target_id"]
        ):
            continue

        keyword = str(
            rule["keyword"]
        )

        if keyword not in answer_text:
            continue

        result.final_sentiment = (
            SentimentLabel.NEGATIVE
        )

        result.override_applied = True

        rule_code = str(
            rule["rule_code"]
        )

        if (
            rule_code
            not in result.override_rule_codes
        ):
            result.override_rule_codes.append(
                rule_code
            )

        matched_reasons.append(
            str(rule["reason"])
        )

        _append_required_evidence(
            result.evidence,
            _keyword_sentence(
                answer_text,
                keyword,
            ),
            evidence_max_items=(
                evidence_max_items
            ),
        )

    if matched_reasons:
        result.override_reason = "；".join(
            matched_reasons
        )

        if not result.reason:
            result.reason = (
                result.override_reason
            )

    apply_hongmao_full_answer_negative_facts(
        result=result,
        target=target,
        answer_text=answer_text,
        evidence_max_items=(
            evidence_max_items
        ),
    )


def apply_hongmao_full_answer_negative_facts(
    *,
    result: SentimentResult,
    target: MentionTarget,
    answer_text: str,
    evidence_max_items: int,
) -> None:
    if (
        target.target_id
        != "hongmao_yaojiu"
    ):
        return

    if (
        not answer_text
        or not any(
            alias
            and alias in answer_text
            for alias in target.aliases
        )
    ):
        return

    matched_reasons: list[str] = []

    for (
        code,
        phrases,
    ) in (
        HONGMAO_FULL_ANSWER_NEGATIVE_FACT_RULES
        .items()
    ):
        for phrase in phrases:
            match_info = (
                _hongmao_unnegated_phrase_match(
                    answer_text,
                    phrase,
                    target.aliases,
                    rule_code=code,
                    suppressions=(
                        result
                        .suppressed_rule_candidates
                    ),
                )
            )

            if match_info is None:
                continue

            result.final_sentiment = (
                SentimentLabel.NEGATIVE
            )

            result.override_applied = True

            if (
                code
                not in result.override_rule_codes
            ):
                result.override_rule_codes.append(
                    code
                )

            matched_reasons.append(
                "鸿茅药酒正文出现明确负面事实："
                f"{phrase}"
            )

            _append_required_evidence(
                result.evidence,
                (
                    match_info.get(
                        "sentence"
                    )
                    or _keyword_sentence(
                        answer_text,
                        phrase,
                    )
                ),
                evidence_max_items=(
                    evidence_max_items
                ),
            )

            break

    if matched_reasons:
        existing_reason = (
            result.override_reason
            or ""
        )

        reason_text = "；".join(
            matched_reasons
        )

        result.override_reason = (
            f"{existing_reason}；{reason_text}"
            if existing_reason
            else reason_text
        )

        if not result.reason:
            result.reason = (
                result.override_reason
            )


def finalize_rule_flags(
    result: SentimentResult,
) -> None:
    """
    完成最终规则状态。

    rule_hit:
        是否命中过业务规则。

    rule_override:
        业务规则是否真正改变模型原始分类。

    override_applied:
        与豆包最终语义一致，
        最终等于 rule_override。
    """

    result.rule_hit = bool(
        result.override_rule_codes
    )

    result.rule_override = bool(
        result.rule_hit
        and result.model_sentiment
        in {
            SentimentLabel.POSITIVE,
            SentimentLabel.NEUTRAL,
            SentimentLabel.NEGATIVE,
        }
        and result.final_sentiment
        in {
            SentimentLabel.POSITIVE,
            SentimentLabel.NEUTRAL,
            SentimentLabel.NEGATIVE,
        }
        and (
            result.model_sentiment
            != result.final_sentiment
        )
    )

    result.override_applied = (
        result.rule_override
    )


def is_negated_match(
    text: str,
    match_start: int,
    match_end: int,
    *,
    negation_terms: list[str] | None = None,
    max_window: int = 18,
) -> dict[str, Any] | None:
    terms = (
        negation_terms
        or NEGATION_PREFIXES
    )

    (
        scope_start,
        scope_end,
        scope_text,
    ) = _clause_scope(
        text,
        match_start,
        match_end,
    )

    prefix = text[
        max(
            scope_start,
            match_start - max_window,
        )
        :match_start
    ]

    suffix = text[
        match_end:
        min(
            scope_end,
            match_end + 8,
        )
    ]

    local_text = text[
        max(
            scope_start,
            match_start - max_window,
        )
        :
        min(
            scope_end,
            match_end + 8,
        )
    ]

    for term in sorted(
        terms,
        key=len,
        reverse=True,
    ):
        if (
            term
            and term in prefix
        ):
            return {
                "negation_term": term,
                "negation_scope_text": (
                    scope_text
                ),
                "local_text": local_text,
            }

    if re.search(
        (
            r"(?:不存在|暂无|没有|未发现)"
            r"[^。！？!?；;\n，,]{0,8}$"
        ),
        prefix,
    ):
        return {
            "negation_term": (
                "implicit_prefix_negation"
            ),
            "negation_scope_text": (
                scope_text
            ),
            "local_text": local_text,
        }

    if (
        re.match(
            r"^(?:要求|通知|问题)",
            suffix,
        )
        and any(
            term in prefix
            for term in [
                "未发现",
                "不存在",
                "暂无",
                "没有",
            ]
        )
    ):
        return {
            "negation_term": (
                "implicit_compound_negation"
            ),
            "negation_scope_text": (
                scope_text
            ),
            "local_text": local_text,
        }

    return None


def _clause_scope(
    text: str,
    start: int,
    end: int,
) -> tuple[int, int, str]:
    left_boundaries = (
        "。！？!?；;\n，,"
    )

    right_boundaries = (
        left_boundaries
    )

    scope_start = max(
        text.rfind(
            ch,
            0,
            start,
        )
        for ch in left_boundaries
    ) + 1

    right_indexes = [
        text.find(
            ch,
            end,
        )
        for ch in right_boundaries
    ]

    right_indexes = [
        index
        for index in right_indexes
        if index >= 0
    ]

    scope_end = (
        min(right_indexes)
        if right_indexes
        else len(text)
    )

    return (
        scope_start,
        scope_end,
        text[
            scope_start:scope_end
        ].strip(),
    )


def _phrase_has_unnegated_match(
    text: str,
    phrase: str,
) -> bool:
    for match in re.finditer(
        re.escape(phrase),
        text,
    ):
        if is_negated_match(
            text,
            match.start(),
            match.end(),
        ):
            continue

        return True

    return False


def _target_relevant_sentences(
    target_context: str,
    target_aliases: list[str] | None,
) -> list[str]:
    if not target_aliases:
        return [
            target_context
        ]

    sentences = re.findall(
        (
            r"[^。！？!?；;\n]+"
            r"[。！？!?；;]?"
        ),
        target_context or "",
    )

    scoped = [
        sentence
        for sentence in sentences
        if any(
            alias
            and alias in sentence
            for alias in target_aliases
        )
    ]

    return (
        scoped
        or [target_context]
    )


def _hongmao_unnegated_phrase_match(
    answer_text: str,
    phrase: str,
    aliases: list[str],
    *,
    rule_code: str | None = None,
    suppressions: (
        list[dict[str, Any]]
        | None
    ) = None,
) -> dict[str, Any] | None:
    if phrase not in answer_text:
        return None

    for sentence in re.findall(
        (
            r"[^。！？!?；;\n]+"
            r"[。！？!?；;]?"
        ),
        answer_text,
    ):
        if (
            phrase not in sentence
            or not any(
                alias
                and alias in sentence
                for alias in aliases
            )
        ):
            continue

        sentence_start = (
            answer_text.find(
                sentence
            )
        )

        for match in re.finditer(
            re.escape(phrase),
            sentence,
        ):
            absolute_start = (
                sentence_start
                + match.start()
            )

            absolute_end = (
                sentence_start
                + match.end()
            )

            negation = is_negated_match(
                answer_text,
                absolute_start,
                absolute_end,
            )

            if negation:
                _record_suppressed_rule_candidate(
                    suppressions,
                    rule_code=rule_code,
                    phrase=phrase,
                    match_start=absolute_start,
                    match_end=absolute_end,
                    negation=negation,
                )

                continue

            return {
                "match_text": phrase,
                "match_start": (
                    absolute_start
                ),
                "match_end": (
                    absolute_end
                ),
                "sentence": (
                    sentence.strip()
                ),
            }

    for match in re.finditer(
        re.escape(phrase),
        answer_text,
    ):
        negation = is_negated_match(
            answer_text,
            match.start(),
            match.end(),
        )

        if negation:
            _record_suppressed_rule_candidate(
                suppressions,
                rule_code=rule_code,
                phrase=phrase,
                match_start=match.start(),
                match_end=match.end(),
                negation=negation,
            )

            continue

        start = max(
            0,
            match.start() - 300,
        )

        end = min(
            len(answer_text),
            match.end() + 300,
        )

        window = answer_text[
            start:end
        ]

        if any(
            alias
            and alias in window
            for alias in aliases
        ):
            return {
                "match_text": phrase,
                "match_start": (
                    match.start()
                ),
                "match_end": (
                    match.end()
                ),
                "sentence": (
                    _keyword_sentence(
                        answer_text,
                        phrase,
                    )
                ),
            }

    return None


def _record_suppressed_rule_candidate(
    suppressions: (
        list[dict[str, Any]]
        | None
    ),
    *,
    rule_code: str | None,
    phrase: str,
    match_start: int,
    match_end: int,
    negation: dict[str, Any],
) -> None:
    if suppressions is None:
        return

    record = {
        "candidate_rule_code": (
            rule_code
        ),
        "candidate_match_text": (
            phrase
        ),
        "match_start": match_start,
        "match_end": match_end,
        "negation_detected": True,
        "negation_term": (
            negation.get(
                "negation_term"
            )
        ),
        "negation_scope_text": (
            negation.get(
                "negation_scope_text"
            )
        ),
        "candidate_suppressed_reason": (
            "negated_match"
        ),
    }

    if record not in suppressions:
        suppressions.append(
            record
        )


def _append_required_evidence(
    evidence: list[str],
    item: str,
    *,
    evidence_max_items: int,
) -> None:
    if (
        not item
        or item in evidence
    ):
        return

    if evidence_max_items <= 0:
        evidence.append(item)
        return

    if (
        len(evidence)
        >= evidence_max_items
    ):
        evidence.pop(0)

    evidence.append(item)


def _keyword_sentence(
    text: str,
    keyword: str,
) -> str:
    pattern = (
        r"[^。！？!?；;\n]*"
        + re.escape(keyword)
        + r"[^。！？!?；;\n]*"
        r"[。！？!?；;]?"
    )

    for match in re.finditer(
        pattern,
        text,
    ):
        sentence = (
            match.group(0).strip()
        )

        if sentence:
            return sentence

    return keyword