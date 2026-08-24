import json
from dataclasses import (
    asdict,
    is_dataclass,
)
from typing import Any


def _to_serializable(
        value: Any,
) -> Any:
    """
    将 dataclass 等对象转换为 JSON 可序列化结果。
    """

    if (
            is_dataclass(value)
            and not isinstance(value, type)
    ):
        return asdict(value)

    return value


def json_bytes(
        value: Any,
) -> bytes:
    """
    按照 geo_package_v1 规则序列化 JSON。
    """

    payload = _to_serializable(
        value
    )

    text = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return text.encode(
        "utf-8"
    )


def jsonl_bytes(
        rows: list[Any],
) -> bytes:
    """
    按照 geo_package_v1 规则序列化 JSONL。
    """

    if not rows:
        return b""

    lines = []

    for row in rows:
        payload = _to_serializable(
            row
        )

        lines.append(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )

    return (
            "\n".join(lines)
            + "\n"
    ).encode("utf-8")
