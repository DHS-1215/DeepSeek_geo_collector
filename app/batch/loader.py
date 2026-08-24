import csv
from pathlib import Path

from app.batch.models import BatchTask
from app.core.enums import GeoMode


REQUIRED_COLUMNS = {
    "question_id",
    "question",
    "mode",
}


def parse_mode(
        value: str,
) -> GeoMode:
    """
    将 CSV 中的模式转换为 GeoMode。
    """

    normalized = (
        value
        .strip()
        .lower()
    )

    if normalized == "quick":
        return GeoMode.QUICK

    if normalized == "expert":
        return GeoMode.EXPERT

    raise ValueError(
        f"unsupported mode: {value}"
    )


def load_batch_tasks(
        csv_path: Path,
        batch_id: str,
) -> list[BatchTask]:
    """
    从 CSV 加载并校验批处理任务。
    """

    tasks: list[BatchTask] = []
    seen_task_ids: set[str] = set()

    with csv_path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
    ) as file:
        reader = csv.DictReader(file)

        fieldnames = set(
            reader.fieldnames or []
        )

        missing_columns = (
            REQUIRED_COLUMNS
            -
            fieldnames
        )

        if missing_columns:
            missing_text = ", ".join(
                sorted(missing_columns)
            )

            raise ValueError(
                "missing required columns: "
                f"{missing_text}"
            )

        for row_number, row in enumerate(
                reader,
                start=2,
        ):
            question_id = (
                row["question_id"]
                .strip()
            )

            question = (
                row["question"]
                .strip()
            )

            mode_raw = (
                row["mode"]
                .strip()
            )

            if not question_id:
                raise ValueError(
                    "question_id cannot be empty "
                    f"at row {row_number}"
                )

            if not question:
                raise ValueError(
                    "question cannot be empty "
                    f"at row {row_number}"
                )

            if not mode_raw:
                raise ValueError(
                    "mode cannot be empty "
                    f"at row {row_number}"
                )

            mode = parse_mode(
                mode_raw
            )

            task_id = (
                f"{batch_id}_"
                f"{question_id}_"
                f"{mode.value}"
            )

            if task_id in seen_task_ids:
                raise ValueError(
                    "duplicate batch task: "
                    f"{question_id}/{mode.value} "
                    f"at row {row_number}"
                )

            seen_task_ids.add(
                task_id
            )

            tasks.append(
                BatchTask(
                    batch_id=batch_id,
                    task_id=task_id,
                    question_id=question_id,
                    question=question,
                    mode=mode,
                )
            )

    return tasks