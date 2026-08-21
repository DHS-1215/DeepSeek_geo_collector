from pathlib import Path

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
            "Q002,测试问题2,expert\n"
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
            == "batch_001_Q001"
    )
