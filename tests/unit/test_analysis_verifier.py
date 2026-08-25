import json
from pathlib import Path

from app.analysis.verifier import (
    verify_analysis_file,
)


def _write_json(
        path: Path,
        data: dict,
) -> None:
    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def _valid_document() -> dict:
    return {
        "schema_version": "geo_analysis_v1",
        "product": {},
        "metrics": {
            "mention_rate": 1.0,
        },
        "mention": {},
        "sentiment": {
            "total_count": 10,
            "positive_count": 3,
            "neutral_count": 5,
            "negative_count": 2,
        },
        "sources": {
            "total_occurrences": 20,
            "top10_occurrences": 10,
        },
    }


def test_verify_valid_analysis_file(
        tmp_path: Path,
) -> None:
    path = tmp_path / "analysis.json"

    _write_json(
        path,
        _valid_document(),
    )

    result = verify_analysis_file(
        path
    )

    assert result.passed is True
    assert result.errors == []


def test_verify_missing_field(
        tmp_path: Path,
) -> None:
    path = tmp_path / "analysis.json"

    data = _valid_document()
    data.pop(
        "sources"
    )

    _write_json(
        path,
        data,
    )

    result = verify_analysis_file(
        path
    )

    assert result.passed is False
    assert (
        "missing field: sources"
        in result.errors
    )


def test_verify_sentiment_count_mismatch(
        tmp_path: Path,
) -> None:
    path = tmp_path / "analysis.json"

    data = _valid_document()

    data["sentiment"][
        "negative_count"
    ] = 8

    _write_json(
        path,
        data,
    )

    result = verify_analysis_file(
        path
    )

    assert result.passed is False
    assert (
        "sentiment count mismatch"
        in result.errors
    )


def test_verify_missing_file(
        tmp_path: Path,
) -> None:
    result = verify_analysis_file(
        tmp_path / "none.json"
    )

    assert result.passed is False