import pytest

from app.analysis.source_top10 import (
    analyze_source_top10,
)
from app.core.enums import (
    GeoMode,
    TaskStatus,
    ValidationStatus,
)
from app.core.models import (
    GeoRunResult,
    GeoSource,
    GeoTask,
    SourceCollection,
    ValidationResult,
)


def _source(
        *,
        order: int,
        url: str,
        title: str = "测试资料",
        site_name: str = "测试网站",
) -> GeoSource:
    return GeoSource(
        occurrence_id=f"S{order}",
        order=order,
        title=title,
        clean_title=title,
        site_name=site_name,
        resolved_url=url,
    )


def _result(
        *,
        task_id: str,
        question_id: str,
        mode: GeoMode,
        sources: list[GeoSource],
        validation_status: (
                ValidationStatus
        ) = ValidationStatus.PASS,
) -> GeoRunResult:
    return GeoRunResult(
        provider="deepseek",

        run_id=f"run_{task_id}",

        task=GeoTask(
            task_id=task_id,
            question_id=question_id,
            question=f"{question_id} 问题",
            mode=mode,
        ),

        answer_text_raw="有效回答",

        answer_text_clean="有效回答",

        sources=SourceCollection(
            sources=sources,
        ),

        validation=ValidationResult(
            status=validation_status,
            is_complete=True,
        ),

        status=TaskStatus.SUCCESS,
    )


def test_same_source_in_same_answer_counts_once() -> None:
    results = [
        _result(
            task_id="Q001_quick",
            question_id="Q001",
            mode=GeoMode.QUICK,
            sources=[
                _source(
                    order=1,
                    url="https://example.com/a",
                ),
                _source(
                    order=5,
                    url="https://example.com/a",
                ),
            ],
        )
    ]

    summary = analyze_source_top10(
        results=results,
        mode=GeoMode.QUICK,
    )

    assert summary.total_occurrences == 1

    assert (
            summary.items[0].occurrence_count
            == 1
    )


def test_tracking_variants_count_as_same_source() -> None:
    results = [
        _result(
            task_id="Q001_quick",
            question_id="Q001",
            mode=GeoMode.QUICK,
            sources=[
                _source(
                    order=1,
                    url=(
                        "https://example.com/a"
                        "?id=1&utm_source=x"
                    ),
                ),
                _source(
                    order=2,
                    url=(
                        "https://example.com/a"
                        "?id=1&source=share"
                    ),
                ),
            ],
        )
    ]

    summary = analyze_source_top10(
        results=results,
        mode=GeoMode.QUICK,
    )

    assert summary.total_occurrences == 1


def test_same_source_across_answers_accumulates() -> None:
    results = [
        _result(
            task_id="Q001_quick",
            question_id="Q001",
            mode=GeoMode.QUICK,
            sources=[
                _source(
                    order=1,
                    url="https://example.com/a",
                ),
            ],
        ),
        _result(
            task_id="Q002_quick",
            question_id="Q002",
            mode=GeoMode.QUICK,
            sources=[
                _source(
                    order=2,
                    url="https://example.com/a",
                ),
            ],
        ),
    ]

    summary = analyze_source_top10(
        results=results,
        mode=GeoMode.QUICK,
    )

    assert summary.total_occurrences == 2

    assert (
            summary.items[0].occurrence_count
            == 2
    )

    assert (
            summary.items[0].question_count
            == 2
    )


def test_same_question_counts_once_for_question_count() -> None:
    results = [
        _result(
            task_id="Q001_quick",
            question_id="Q001",
            mode=GeoMode.QUICK,
            sources=[
                _source(
                    order=1,
                    url="https://example.com/a",
                ),
            ],
        ),
        _result(
            task_id="Q001_expert",
            question_id="Q001",
            mode=GeoMode.EXPERT,
            sources=[
                _source(
                    order=1,
                    url="https://example.com/a",
                ),
            ],
        ),
    ]

    summary = analyze_source_top10(
        results=results,
        mode=None,
    )

    assert summary.total_occurrences == 2

    assert (
            summary.items[0].question_count
            == 1
    )


def test_invalid_answer_sources_are_excluded() -> None:
    results = [
        _result(
            task_id="Q001_quick",
            question_id="Q001",
            mode=GeoMode.QUICK,
            sources=[
                _source(
                    order=1,
                    url="https://example.com/a",
                ),
            ],
            validation_status=(
                ValidationStatus.FAIL
            ),
        ),
    ]

    summary = analyze_source_top10(
        results=results,
        mode=GeoMode.QUICK,
    )

    assert summary.total_occurrences == 0
    assert summary.items == []


def test_mode_filter() -> None:
    results = [
        _result(
            task_id="Q001_quick",
            question_id="Q001",
            mode=GeoMode.QUICK,
            sources=[
                _source(
                    order=1,
                    url="https://example.com/quick",
                ),
            ],
        ),
        _result(
            task_id="Q001_expert",
            question_id="Q001",
            mode=GeoMode.EXPERT,
            sources=[
                _source(
                    order=1,
                    url="https://example.com/expert",
                ),
            ],
        ),
    ]

    summary = analyze_source_top10(
        results=results,
        mode=GeoMode.QUICK,
    )

    assert summary.total_occurrences == 1

    assert (
            summary.items[0].canonical_url
            == "https://example.com/quick"
    )


def test_source_share() -> None:
    results = [
        _result(
            task_id="Q001_quick",
            question_id="Q001",
            mode=GeoMode.QUICK,
            sources=[
                _source(
                    order=1,
                    url="https://example.com/a",
                ),
                _source(
                    order=2,
                    url="https://example.com/b",
                ),
            ],
        ),
        _result(
            task_id="Q002_quick",
            question_id="Q002",
            mode=GeoMode.QUICK,
            sources=[
                _source(
                    order=1,
                    url="https://example.com/a",
                ),
            ],
        ),
    ]

    summary = analyze_source_top10(
        results=results,
        mode=GeoMode.QUICK,
    )

    assert summary.total_occurrences == 3

    assert (
            summary.items[0].occurrence_count
            == 2
    )

    assert (
            summary.items[0].share
            == pytest.approx(
        2 / 3
    )
    )


def test_top10_share() -> None:
    sources = [
        _source(
            order=index,
            url=(
                f"https://example.com/{index}"
            ),
        )
        for index in range(
            1,
            12,
        )
    ]

    results = [
        _result(
            task_id="Q001_quick",
            question_id="Q001",
            mode=GeoMode.QUICK,
            sources=sources,
        )
    ]

    summary = analyze_source_top10(
        results=results,
        mode=GeoMode.QUICK,
    )

    assert summary.total_occurrences == 11

    assert summary.top10_occurrences == 10

    assert (
            summary.outside_top10_occurrences
            == 1
    )

    assert summary.top10_share == (
        pytest.approx(
            10 / 11
        )
    )

    assert (
            summary.outside_top10_share
            == pytest.approx(
        1 / 11
    )
    )

    assert len(summary.items) == 10
