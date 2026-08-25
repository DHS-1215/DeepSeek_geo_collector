import json
from pathlib import Path
from typing import Any


def export_analysis_json(
        *,
        document: dict[str, Any],
        output_path: Path,
) -> Path:
    """
    将 geo_analysis_v1 document
    导出为 JSON 文件。

    特性：
    - UTF-8 编码
    - 中文不转义
    - 缩进格式化
    - 自动创建目录
    """

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
            "w",
            encoding="utf-8",
    ) as file:
        json.dump(
            document,
            file,
            ensure_ascii=False,
            indent=2,
        )

        file.write("\n")

    return output_path
