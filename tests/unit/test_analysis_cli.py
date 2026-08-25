from pathlib import Path

import app.analysis.__main__ as cli


def test_parse_args():

    args = cli.parse_args(
        [
            "--package",
            "a.zip",
            "--output-dir",
            "output",
            "--product-id",
            "hongmao",
            "--product-name",
            "鸿茅药酒",
        ]
    )

    assert args.package == Path(
        "a.zip"
    )

    assert args.product_id == "hongmao"

    assert args.product_name == "鸿茅药酒"