import json

from pathlib import Path

from app.analysis.exporter import (
    export_analysis_json,
)


def test_export_analysis_json(
        tmp_path: Path,
) -> None:
    document = {
        "schema_version": (
            "geo_analysis_v1"
        ),
        "product": {
            "product_name": (
                "鸿茅药酒"
            )
        },
    }

    output_path = (
            tmp_path
            /
            "analysis.json"
    )

    result = export_analysis_json(
        document=document,
        output_path=output_path,
    )

    assert result == output_path
    assert output_path.exists()

    content = (
        output_path
        .read_text(
            encoding="utf-8"
        )
    )

    assert "鸿茅药酒" in content
    assert "\\u9e3f" not in content

    loaded = json.loads(
        content
    )

    assert (
            loaded["schema_version"]
            ==
            "geo_analysis_v1"
    )


def test_export_analysis_json_creates_parent(
        tmp_path: Path,
) -> None:
    output_path = (
            tmp_path
            /
            "nested"
            /
            "analysis.json"
    )

    export_analysis_json(
        document={},
        output_path=output_path,
    )

    assert output_path.exists()
