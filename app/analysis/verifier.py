from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class AnalysisVerificationResult:
    """
    GEO Analysis 文件校验结果。
    """

    passed: bool

    errors: list[str]

    warnings: list[str]


class AnalysisVerificationError(Exception):
    """
    Analysis 校验异常。
    """


def verify_analysis_file(
        path: Path,
) -> AnalysisVerificationResult:
    """
    校验 GEO analysis JSON 文件。
    """

    errors: list[str] = []
    warnings: list[str] = []

    if not path.exists():
        return AnalysisVerificationResult(
            passed=False,
            errors=[
                f"file not found: {path}"
            ],
            warnings=[],
        )

    try:
        document = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except json.JSONDecodeError:
        return AnalysisVerificationResult(
            passed=False,
            errors=[
                "invalid json"
            ],
            warnings=[],
        )

    _validate_schema(
        document,
        errors,
    )

    _validate_metrics(
        document,
        errors,
    )

    _validate_sentiment(
        document,
        errors,
    )

    _validate_sources(
        document,
        errors,
    )

    return AnalysisVerificationResult(
        passed=not errors,
        errors=errors,
        warnings=warnings,
    )


def _validate_schema(
        document: Any,
        errors: list[str],
) -> None:
    if not isinstance(
            document,
            dict,
    ):
        errors.append(
            "document must be object"
        )
        return

    required_fields = {
        "schema_version",
        "product",
        "metrics",
        "mention",
        "sentiment",
        "sources",
    }

    missing = (
            required_fields
            -
            set(document.keys())
    )

    for field in sorted(missing):
        errors.append(
            f"missing field: {field}"
        )


def _validate_metrics(
        document: dict[str, Any],
        errors: list[str],
) -> None:
    metrics = document.get(
        "metrics"
    )

    if not isinstance(
            metrics,
            dict,
    ):
        return

    for key, value in metrics.items():
        if not isinstance(
                value,
                (int, float),
        ):
            continue

        if "rate" in key and not (
                0 <= value <= 1
        ):
            errors.append(
                f"invalid rate range: {key}"
            )


def _validate_sentiment(
        document: dict[str, Any],
        errors: list[str],
) -> None:
    sentiment = document.get(
        "sentiment"
    )

    if not isinstance(
            sentiment,
            dict,
    ):
        return

    total = sentiment.get(
        "total_count"
    )

    positive = sentiment.get(
        "positive_count",
        0,
    )

    neutral = sentiment.get(
        "neutral_count",
        0,
    )

    negative = sentiment.get(
        "negative_count",
        0,
    )

    if all(
            isinstance(
                item,
                int,
            )
            for item in [
                total,
                positive,
                neutral,
                negative,
            ]
    ):
        if (
                positive
                +
                neutral
                +
                negative
                !=
                total
        ):
            errors.append(
                "sentiment count mismatch"
            )


def _validate_sources(
        document: dict[str, Any],
        errors: list[str],
) -> None:
    sources = document.get(
        "sources"
    )

    if not isinstance(
            sources,
            dict,
    ):
        return

    total = sources.get(
        "total_occurrences"
    )

    top10 = sources.get(
        "top10_occurrences"
    )

    if (
            isinstance(total, int)
            and isinstance(top10, int)
            and top10 > total
    ):
        errors.append(
            "top10 occurrences exceed total occurrences"
        )
