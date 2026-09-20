from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_EXAMPLE = PROJECT_ROOT / ".env.example"
ENV_FILE = PROJECT_ROOT / ".env"

MODEL_NAME = "qwen2.5:7b"


def print_step(title: str) -> None:
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def find_chrome() -> Path | None:
    candidates: list[Path] = []

    local_app_data = os.getenv("LOCALAPPDATA")
    program_files = os.getenv("PROGRAMFILES")
    program_files_x86 = os.getenv("PROGRAMFILES(X86)")

    if local_app_data:
        candidates.append(
            Path(local_app_data)
            / "Google"
            / "Chrome"
            / "Application"
            / "chrome.exe"
        )

    if program_files:
        candidates.append(
            Path(program_files)
            / "Google"
            / "Chrome"
            / "Application"
            / "chrome.exe"
        )

    if program_files_x86:
        candidates.append(
            Path(program_files_x86)
            / "Google"
            / "Chrome"
            / "Application"
            / "chrome.exe"
        )

    candidates.extend(
        [
            Path(
                r"D:\playwright_browsers"
                r"\chrome-win64"
                r"\chrome.exe"
            ),
            Path(
                r"C:\playwright_browsers"
                r"\chrome-win64"
                r"\chrome.exe"
            ),
        ]
    )

    for path in candidates:
        if path.is_file():
            return path

    return None


def build_env(chrome_path: Path | None) -> None:
    if not ENV_EXAMPLE.is_file():
        raise RuntimeError(
            ".env.example not found."
        )

    # 已有 .env 时不直接覆盖用户配置，
    # 只在新电脑首次初始化时生成。
    if ENV_FILE.exists():
        print(
            f"[OK] Existing .env found: "
            f"{ENV_FILE}"
        )
        return

    content = ENV_EXAMPLE.read_text(
        encoding="utf-8"
    )

    if chrome_path:
        chrome_value = str(chrome_path)

        lines = []

        for line in content.splitlines():
            if line.startswith(
                "CHROMIUM_EXECUTABLE_PATH="
            ):
                line = (
                    "CHROMIUM_EXECUTABLE_PATH="
                    f"{chrome_value}"
                )

            lines.append(line)

        content = "\n".join(lines) + "\n"

    else:
        lines = []

        for line in content.splitlines():
            if line.startswith(
                "CHROMIUM_EXECUTABLE_PATH="
            ):
                line = (
                    "CHROMIUM_EXECUTABLE_PATH="
                )

            lines.append(line)

        content = "\n".join(lines) + "\n"

    ENV_FILE.write_text(
        content,
        encoding="utf-8",
    )

    print(
        f"[OK] Created .env: "
        f"{ENV_FILE}"
    )


def create_directories() -> None:
    directories = [
        PROJECT_ROOT / "browser_profile",
        PROJECT_ROOT / "output",
        PROJECT_ROOT / "output" / "package",
    ]

    for directory in directories:
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    print(
        "[OK] Runtime directories ready."
    )


def check_ollama() -> bool:
    executable = shutil.which(
        "ollama"
    )

    if executable is None:
        print(
            "[WARN] Ollama was not found."
        )
        print(
            "       Install Ollama before "
            "running sentiment analysis."
        )
        return False

    print(
        f"[OK] Ollama found: {executable}"
    )

    try:
        result = subprocess.run(
            [
                executable,
                "list",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except Exception as exc:
        print(
            "[WARN] Unable to query Ollama:"
        )
        print(
            f"       {exc}"
        )
        return False

    output = (
        result.stdout
        + "\n"
        + result.stderr
    )

    if MODEL_NAME in output:
        print(
            f"[OK] Ollama model found: "
            f"{MODEL_NAME}"
        )
        return True

    print(
        f"[WARN] Ollama model missing: "
        f"{MODEL_NAME}"
    )
    print(
        "       Run:"
    )
    print(
        f"       ollama pull {MODEL_NAME}"
    )

    return False


def run_smoke_test() -> bool:
    print(
        "[INFO] Running project import test..."
    )

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from app.core.config "
                "import load_settings; "
                "s = load_settings(); "
                "print("
                "'DeepSeek URL:', "
                "s.deepseek_url"
                "); "
                "print("
                "'Browser profile:', "
                "s.browser_profile_dir"
                "); "
                "print("
                "'Output:', "
                "s.output_dir"
                "); "
                "print("
                "'Chrome:', "
                "s.chromium_executable_path"
                ")"
            ),
        ],
        cwd=PROJECT_ROOT,
        check=False,
    )

    if result.returncode != 0:
        print(
            "[ERROR] Project import test failed."
        )
        return False

    print(
        "[OK] Project import test passed."
    )
    return True


def main() -> int:
    print_step(
        "DeepSeek GEO Collector - "
        "Environment Configuration"
    )

    print(
        f"[INFO] Project: {PROJECT_ROOT}"
    )
    print(
        f"[INFO] Python: {sys.version.split()[0]}"
    )

    print_step(
        "Detecting Chrome"
    )

    chrome_path = find_chrome()

    if chrome_path:
        print(
            f"[OK] Chrome found: "
            f"{chrome_path}"
        )
    else:
        print(
            "[WARN] Chrome was not detected."
        )
        print(
            "       Install Google Chrome "
            "before real collection."
        )

    print_step(
        "Creating Environment Configuration"
    )

    build_env(
        chrome_path
    )

    create_directories()

    print_step(
        "Checking Ollama"
    )

    ollama_ready = check_ollama()

    print_step(
        "Running Smoke Test"
    )

    smoke_ok = run_smoke_test()

    print_step(
        "Setup Summary"
    )

    print(
        f"Chrome : "
        f"{'OK' if chrome_path else 'MISSING'}"
    )
    print(
        f"Ollama : "
        f"{'OK' if ollama_ready else 'CHECK REQUIRED'}"
    )
    print(
        f"Project: "
        f"{'OK' if smoke_ok else 'FAILED'}"
    )

    if not smoke_ok:
        return 1

    if not chrome_path:
        print()
        print(
            "[WARN] Setup completed, "
            "but Chrome must be installed "
            "before collection."
        )

    if not ollama_ready:
        print()
        print(
            "[WARN] Setup completed, "
            "but Ollama sentiment analysis "
            "is not ready."
        )

    print()
    print(
        "[SUCCESS] Environment "
        "configuration completed."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
