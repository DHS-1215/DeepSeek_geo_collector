import pytest

from app.package.source_utils import (
    canonicalize_url,
    finalize_source_rows,
    normalize_raw_url,
)

from app.package.source_utils import normalize_url


def test_normalize_raw_url() -> None:
    result = normalize_raw_url(
        "HTTPS://Example.COM/a/b/#fragment"
    )

    assert result == "https://example.com/a/b"


def test_normalize_raw_url_decodes_html_entities() -> None:
    result = normalize_raw_url(
        "https://example.com/page?a=1&amp;b=2"
    )

    assert result == (
        "https://example.com/page?a=1&b=2"
    )


def test_canonicalize_url_removes_tracking_parameters() -> None:
    result = canonicalize_url(
        "https://example.com/page"
        "?utm_source=test"
        "&from=share"
        "&id=123"
    )

    assert result == (
        "https://example.com/page?id=123"
    )


def test_canonicalize_url_sorts_query_parameters() -> None:
    result = canonicalize_url(
        "https://example.com/page?b=2&a=1"
    )

    assert result == (
        "https://example.com/page?a=1&b=2"
    )


def test_finalize_source_rows_removes_normalized_duplicate() -> None:
    rows = [
        {
            "answer_id": "answer_001",
            "task_id": "Q001_expert",
            "question_id": "Q001",
            "mode_code": "expert",
            "source_order": 1,
            "source_url_raw": (
                "https://example.com/page?id=1"
            ),
            "source_title_raw": "标题1",
            "occurrence_id": "R1_S1",
        },
        {
            "answer_id": "answer_001",
            "task_id": "Q001_expert",
            "question_id": "Q001",
            "mode_code": "expert",
            "source_order": 1,
            "source_url_raw": (
                "https://example.com/page"
                "?id=1&utm_source=test"
            ),
            "source_title_raw": "标题1",
            "occurrence_id": "R1_S2",
        },
    ]

    finalized, diagnostics = (
        finalize_source_rows(
            "batch_001",
            rows,
        )
    )

    assert len(finalized) == 1

    assert (
            diagnostics[
                "exact_duplicate_rows_removed"
            ]
            == 1
    )


def test_finalize_source_rows_generates_stable_occurrence_id() -> None:
    rows = [
        {
            "answer_id": "answer_001",
            "task_id": "Q001_expert",
            "question_id": "Q001",
            "mode_code": "expert",
            "source_order": 1,
            "source_url_raw": (
                "https://example.com/page"
            ),
        }
    ]

    first, _ = finalize_source_rows(
        "batch_001",
        rows,
    )

    second, _ = finalize_source_rows(
        "batch_001",
        rows,
    )

    assert (
            first[0]["occurrence_id"]
            == second[0]["occurrence_id"]
    )

    assert first[0]["occurrence_id"].startswith(
        "batch_001_0001_"
    )


def test_source_order_conflict_raises_error() -> None:
    rows = [
        {
            "answer_id": "answer_001",
            "source_order": 1,
            "source_url_raw": (
                "https://example.com/a"
            ),
        },
        {
            "answer_id": "answer_001",
            "source_order": 1,
            "source_url_raw": (
                "https://example.com/b"
            ),
        },
    ]

    with pytest.raises(
            RuntimeError,
            match="source_order_conflict",
    ):
        finalize_source_rows(
            "batch_001",
            rows,
        )


def test_normalize_url() -> None:
    assert (
            normalize_url(
                "HTTP://Example.COM/test/?a=1"
            )
            == "http://example.com/test"
    )


def test_normalize_url_removes_query() -> None:
    assert (
            normalize_url(
                "https://example.com/page?id=1"
            )
            == "https://example.com/page"
    )


def test_normalize_url_none() -> None:
    assert (
            normalize_url(None)
            is None
    )
