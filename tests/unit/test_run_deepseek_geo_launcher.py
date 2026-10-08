from pathlib import Path
from types import SimpleNamespace

import scripts.run_deepseek_geo as launcher


def test_launcher_propagates_internal_error_exit_code(
        monkeypatch,
        tmp_path: Path,
) -> None:
    csv_path = (
        tmp_path / "questions.csv"
    )
    csv_path.write_text(
        "question_id,question,mode\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        launcher,
        "OUTPUT_DIR",
        tmp_path / "output",
    )

    monkeypatch.setattr(
        launcher,
        "choose_batch_id",
        lambda product_id: (
            "test_product_20261008_000000"
        ),
    )

    monkeypatch.setattr(
        launcher.subprocess,
        "run",
        lambda *args, **kwargs: (
            SimpleNamespace(
                returncode=5,
            )
        ),
    )

    exit_code = launcher.run_pipeline(
        {
            "product_id": "test_product",
            "product_name": "test product",
            "csv_path": csv_path,
        }
    )

    assert exit_code == 5
