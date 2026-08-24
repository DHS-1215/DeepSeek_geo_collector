import json

from app.package.models import (
    PackageTaskRow,
)
from app.package.serialization import (
    json_bytes,
    jsonl_bytes,
)


def test_jsonl_bytes_uses_compact_sorted_json() -> None:
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

    content = jsonl_bytes(
        rows
    )

    assert content.endswith(
        b"\n"
    )

    parsed = json.loads(
        content
        .decode("utf-8")
        .strip()
    )

    assert (
            parsed["task_id"]
            == "Q001_quick"
    )

    assert (
            parsed["platform_code"]
            == "deepseek"
    )


def test_jsonl_bytes_serializes_all_rows() -> None:
    rows = [
        PackageTaskRow(
            task_id="Q001_quick",
            batch_id="batch_001",
            platform_code="deepseek",
            question_id="Q001",
            question="测试问题1",
            mode_code="quick",
            task_status="success",
            error_code=None,
            error_message=None,
            created_at=None,
            finished_at=None,
            elapsed_seconds=1.0,
        ),
        PackageTaskRow(
            task_id="Q001_expert",
            batch_id="batch_001",
            platform_code="deepseek",
            question_id="Q001",
            question="测试问题1",
            mode_code="expert",
            task_status="success",
            error_code=None,
            error_message=None,
            created_at=None,
            finished_at=None,
            elapsed_seconds=2.0,
        ),
        PackageTaskRow(
            task_id="Q002_quick",
            batch_id="batch_001",
            platform_code="deepseek",
            question_id="Q002",
            question="测试问题2",
            mode_code="quick",
            task_status="failed",
            error_code=None,
            error_message="answer timed out",
            created_at=None,
            finished_at=None,
            elapsed_seconds=3.0,
        ),
    ]

    content = jsonl_bytes(
        rows
    )

    lines = (
        content
        .decode("utf-8")
        .strip()
        .splitlines()
    )

    assert len(lines) == 3

    parsed_rows = [
        json.loads(line)
        for line in lines
    ]

    assert [
               row["task_id"]
               for row in parsed_rows
           ] == [
               "Q001_quick",
               "Q001_expert",
               "Q002_quick",
           ]

    assert (
            parsed_rows[0]["mode_code"]
            == "quick"
    )

    assert (
            parsed_rows[1]["mode_code"]
            == "expert"
    )

    assert (
            parsed_rows[2]["task_status"]
            == "failed"
    )

    assert (
            parsed_rows[2]["error_message"]
            == "answer timed out"
    )


def test_empty_jsonl_returns_empty_bytes() -> None:
    assert (
            jsonl_bytes([])
            == b""
    )
