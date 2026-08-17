import json

from app.package.models import PackageTaskRow
from app.package.serialization import jsonl_bytes, json_bytes


def test_json_bytes_uses_compact_sorted_json() -> None:
    rows = [
        PackageTaskRow(
            task_id="Q001_quick",
            batch_id="batch_001",
            platform_code="deepseek",
            question_id="Q001",
            question="测试问题",
            mode_code="quick",
            task_status="success",
            error_code=None,
            error_message=None,
            created_at=None,
            finished_at=None,
            elapsed_seconds=1.5,
        )
    ]

    content = jsonl_bytes(rows)
    assert content.endswith(b"\n")

    parsed = json.loads(
        content.decode("utf-8").strip()
    )

    assert parsed['task_id'] == 'Q001_quick'
    assert parsed['platform_code'] == 'deepseek'


def test_empty_jsonl_returns_empty_bytes() -> None:
    assert jsonl_bytes([]) == b""
