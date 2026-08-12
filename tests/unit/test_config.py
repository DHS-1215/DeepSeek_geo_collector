import pytest

from app.core.config import PROJECT_ROOT, load_settings
from app.core.exceptions import ConfigurationError


def test_load_settings_uses_default_values(monkeypatch: pytest.MonkeyPatch) -> None:
    env_names = [
        "DEEPSEEK_URL",
        "BROWSER_PROFILE_DIR",
        "OUTPUT_DIR",
        "HEADLESS",
        "DEFAULT_TIMEOUT_SECONDS",
        "QUICK_MAX_WAIT_SECONDS",
        "EXPERT_MAX_WAIT_SECONDS",
        "NETWORK_RETRY_TIMES",
        "NETWORK_RETRY_INTERVAL_SECONDS",
        "SAVE_RAW_HTML_ON_ERROR",
        "LOG_LEVEL",
    ]

    for name in env_names:
        monkeypatch.delenv(name, raising=False)

    settings = load_settings()

    assert settings.deepseek_url == "https://chat.deepseek.com"

    assert settings.browser_profile_dir == PROJECT_ROOT / "browser_profile"
    assert settings.output_dir == PROJECT_ROOT / "output"

    assert settings.headless is False

    assert settings.default_timeout_seconds == 30

    assert settings.quick_max_wait_seconds == 180
    assert settings.expert_max_wait_seconds == 360

    assert settings.network_retry_times == 2
    assert settings.network_retry_interval_seconds == 3

    assert settings.save_raw_html_on_error is True

    assert settings.log_level == "INFO"


def test_load_settings_reads_environment_variables(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HEADLESS", "true")
    monkeypatch.setenv("QUICK_MAX_WAIT_SECONDS", "200")
    monkeypatch.setenv("LOG_LEVEL", "debug")

    settings = load_settings()

    assert settings.headless is True
    assert settings.quick_max_wait_seconds == 200
    assert settings.log_level == "DEBUG"


def test_invalid_boolean_environment_variable_raises_error(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HEADLESS", "maybe")

    with pytest.raises(ConfigurationError):
        load_settings()


def test_invalid_integer_environment_variable_raises_error(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("QUICK_MAX_WAIT_SECONDS", "abc")

    with pytest.raises(ConfigurationError):
        load_settings()


def test_non_positive_timeout_raises_error(
        monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("QUICK_MAX_WAIT_SECONDS", "0")

    with pytest.raises(
            ConfigurationError,
            match="QUICK_MAX_WAIT_SECONDS",
    ):
        load_settings()
