from pathlib import Path
import pytest
from app.batch.loader import (
    load_batch_tasks,
)
from app.core.enums import GeoMode


def test_load_batch_tasks(
        tmp_path: Path,
):
    csv_file = tmp_path / "questions.csv"

    csv_file.write_text(
        (
            "question_id,question,mode\n"
            "Q001,测试问题1,quick\n"
            "Q001,测试问题1,expert\n"
        ),
        encoding="utf-8",
    )

    tasks = load_batch_tasks(
        csv_file,
        "batch_001",
    )

    assert len(tasks) == 2

    assert (
            tasks[0].question_id
            == "Q001"
    )

    assert (
            tasks[0].mode
            == GeoMode.QUICK
    )

    assert (
            tasks[1].mode
            == GeoMode.EXPERT
    )

    assert (
            tasks[0].task_id
            == "batch_001_Q001_quick"
    )

    assert (
            tasks[1].task_id
            == "batch_001_Q001_expert"
    )

    assert (
            tasks[0].task_id
            != tasks[1].task_id
    )


def test_load_batch_tasks_rejects_missing_columns(
        tmp_path: Path,
):
    csv_file = tmp_path / "questions.csv"

    csv_file.write_text(
        (
            "question_id,question\n"
            "Q001,测试问题\n"
        ),
        encoding="utf-8",
    )

    with pytest.raises(
            ValueError,
            match="missing required columns",
    ):
        load_batch_tasks(
            csv_file,
            "batch_001",
        )


def test_load_batch_tasks_rejects_empty_question(
        tmp_path: Path,
):
    csv_file = tmp_path / "questions.csv"

    csv_file.write_text(
        (
            "question_id,question,mode\n"
            "Q001,,quick\n"
        ),
        encoding="utf-8",
    )

    with pytest.raises(
            ValueError,
            match="question cannot be empty",
    ):
        load_batch_tasks(
            csv_file,
            "batch_001",
        )


def test_load_batch_tasks_rejects_invalid_mode(
        tmp_path: Path,
):
    csv_file = tmp_path / "questions.csv"

    csv_file.write_text(
        (
            "question_id,question,mode\n"
            "Q001,测试问题,unknown\n"
        ),
        encoding="utf-8",
    )

    with pytest.raises(
            ValueError,
            match="unsupported mode",
    ):
        load_batch_tasks(
            csv_file,
            "batch_001",
        )


def test_load_batch_tasks_allows_empty_data(
        tmp_path: Path,
):
    csv_file = tmp_path / "questions.csv"

    csv_file.write_text(
        "question_id,question,mode\n",
        encoding="utf-8",
    )

    tasks = load_batch_tasks(
        csv_file,
        "batch_001",
    )

    assert tasks == []


def test_load_batch_tasks_rejects_duplicate_task(
        tmp_path: Path,
):
    csv_file = tmp_path / "questions.csv"

    csv_file.write_text(
        (
            "question_id,question,mode\n"
            "Q001,测试问题,quick\n"
            "Q001,测试问题,quick\n"
        ),
        encoding="utf-8",
    )

    with pytest.raises(
            ValueError,
            match="duplicate batch task",
    ):
        load_batch_tasks(
            csv_file,
            "batch_001",
        )
