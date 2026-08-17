import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

from app.core.exceptions import ConfigurationError

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _get_bool_env(name: str, default: bool) -> bool:
    """读取布尔类型环境变量。"""

    raw_value = os.getenv(name)

    if raw_value is None:
        return default

    normalized = raw_value.strip().lower()

    if normalized in {"1", "true", "yes", "on"}:
        return True

    if normalized in {"0", "false", "no", "off"}:
        return False

    raise ConfigurationError(
        f"Invalid boolean environment variable: {name}={raw_value!r}"
    )


def _get_int_env(name: str, default: int) -> int:
    """读取整数类型环境变量。"""

    raw_value = os.getenv(name)

    if raw_value is None:
        return default

    try:
        return int(raw_value)
    except ValueError as exc:
        raise ConfigurationError(
            f"Invalid integer environment variable: {name}={raw_value!r}"
        ) from exc


@dataclass(frozen=True, slots=True)
class Settings:
    """DeepSeek GEO Collector 运行配置。"""

    deepseek_url: str

    browser_profile_dir: Path
    output_dir: Path

    headless: bool

    default_timeout_seconds: int

    quick_max_wait_seconds: int
    expert_max_wait_seconds: int

    network_retry_times: int
    network_retry_interval_seconds: int

    save_raw_html_on_error: bool

    log_level: str

    chromium_executable_path: str | None = None


def load_settings(
        env_file: Path | None = PROJECT_ROOT / ".env",
) -> Settings:
    """读取项目配置。"""

    if env_file is not None:
        load_dotenv(
            env_file,
            override=False,
        )

    browser_profile_dir = _get_path_env(
        "BROWSER_PROFILE_DIR",
        PROJECT_ROOT / "browser_profile",
    )

    output_dir = _get_path_env(
        "OUTPUT_DIR",
        PROJECT_ROOT / "output",
    )

    settings = Settings(
        deepseek_url=os.getenv(
            "DEEPSEEK_URL",
            "https://chat.deepseek.com",
        ),

        browser_profile_dir=browser_profile_dir,
        output_dir=output_dir,
        headless=_get_bool_env(
            "HEADLESS",
            False,
        ),
        default_timeout_seconds=_get_int_env(
            "DEFAULT_TIMEOUT_SECONDS",
            30,
        ),
        quick_max_wait_seconds=_get_int_env(
            "QUICK_MAX_WAIT_SECONDS",
            180,
        ),

        chromium_executable_path=(
                os.getenv("CHROMIUM_EXECUTABLE_PATH")
                or None
        ),

        expert_max_wait_seconds=_get_int_env(
            "EXPERT_MAX_WAIT_SECONDS",
            360,
        ),
        network_retry_times=_get_int_env(
            "NETWORK_RETRY_TIMES",
            2,
        ),
        network_retry_interval_seconds=_get_int_env(
            "NETWORK_RETRY_INTERVAL_SECONDS",
            3,
        ),
        save_raw_html_on_error=_get_bool_env(
            "SAVE_RAW_HTML_ON_ERROR",
            True,
        ),
        log_level=os.getenv(
            "LOG_LEVEL",
            "INFO",
        ).upper(),
    )

    _validate_settings(settings)

    return settings


def _validate_settings(settings: Settings) -> None:
    """检查配置值是否处于合理范围。"""

    if settings.default_timeout_seconds <= 0:
        raise ConfigurationError(
            "DEFAULT_TIMEOUT_SECONDS must be greater than 0"
        )

    if settings.quick_max_wait_seconds <= 0:
        raise ConfigurationError(
            "QUICK_MAX_WAIT_SECONDS must be greater than 0"
        )

    if settings.expert_max_wait_seconds <= 0:
        raise ConfigurationError(
            "EXPERT_MAX_WAIT_SECONDS must be greater than 0"
        )

    if settings.network_retry_times < 0:
        raise ConfigurationError(
            "NETWORK_RETRY_TIMES must be greater than or equal to 0"
        )

    if settings.network_retry_interval_seconds < 0:
        raise ConfigurationError(
            "NETWORK_RETRY_INTERVAL_SECONDS must be greater than or equal to 0"
        )


def _get_path_env(
        name: str,
        default: Path,
) -> Path:
    """读取路径环境变量，相对路径基于项目根目录解析。"""

    raw_value = os.getenv(name)

    if not raw_value:
        return default

    path = Path(raw_value)

    if path.is_absolute():
        return path

    return PROJECT_ROOT / path
