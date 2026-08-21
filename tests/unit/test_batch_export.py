from pathlib import Path

from app.batch.export import (
    export_batch_package,
)
from app.batch.models import (
    BatchResult,
)


def test_export_batch_package(
        monkeypatch,
        tmp_path: Path,
):
    called = {}

    def fake_export(
            **kwargs,
    ):
        called.update(kwargs)

        return (
                tmp_path
                / "test.zip"
        )

    monkeypatch.setattr(
        "app.batch.export.export_geo_package",
        fake_export,
    )

    result = BatchResult(
        batch_id="batch_001",
    )

    output = export_batch_package(
        result=result,
        output_dir=tmp_path,
        product_id="test_product",
        product_name="测试产品",
    )

    assert output.name == "test.zip"

    assert (
            called["batch_id"]
            == "batch_001"
    )

    assert (
            called["results"]
            == []
    )

    assert (
            called["product_id"]
            == "test_product"
    )
