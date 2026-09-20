from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = PROJECT_ROOT / "dist"

EXCLUDED_DIRS = {
    ".git",
    ".idea",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "browser_profile",
    "output",
    "dist",
}

EXCLUDED_FILES = {
    ".env",
}

EXCLUDED_SUFFIXES = {
    ".pyc",
    ".pyo",
}


def should_exclude(path: Path) -> bool:
    relative = path.relative_to(PROJECT_ROOT)

    if any(
        part in EXCLUDED_DIRS
        for part in relative.parts
    ):
        return True

    if path.name in EXCLUDED_FILES:
        return True

    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return True

    return False


def main() -> int:
    DIST_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    zip_path = (
        DIST_DIR
        / f"deepseek_geo_collector_portable_{timestamp}.zip"
    )

    file_count = 0

    with ZipFile(
        zip_path,
        "w",
        compression=ZIP_DEFLATED,
    ) as archive:

        for path in PROJECT_ROOT.rglob("*"):
            if not path.is_file():
                continue

            if should_exclude(path):
                continue

            archive.write(
                path,
                path.relative_to(PROJECT_ROOT),
            )

            file_count += 1

    print("=" * 60)
    print("DeepSeek GEO Collector - Portable Package")
    print("=" * 60)
    print()
    print(f"[OK] Files: {file_count}")
    print(f"[OK] Package: {zip_path}")
    print()
    print(
        "Copy this ZIP to another Windows PC, "
        "extract it, then run setup_new_pc.bat."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
