import csv
from pathlib import Path

from app.batch.models import BatchTask
from app.core.enums import GeoMode


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
    从 CSV 加载批处理任务。
    """

    tasks: list[BatchTask] = []

    with csv_path.open(
            "r",
            encoding="utf-8",
            newline="",
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            tasks.append(
                BatchTask(
                    batch_id=batch_id,
                    task_id=(
                        f"{batch_id}_"
                        f"{row['question_id']}"
                    ),
                    question_id=(
                        row["question_id"]
                    ),
                    question=(
                        row["question"]
                    ),
                    mode=parse_mode(
                        row["mode"]
                    ),
                )
            )

    return tasks
