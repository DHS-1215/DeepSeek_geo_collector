import pytest

from app.analysis.sentiment_config import (
    load_sentiment_config,
)
from app.core.exceptions import (
    ConfigurationError,
)


def test_default_sentiment_config(
        monkeypatch,
) -> None:
    names = [
        name
        for name
        in list(__import__("os").environ)
        if name.startswith(
            "SENTIMENT_"
        )
    ]

    for name in names:
        monkeypatch.delenv(
            name,
            raising=False,
        )

    config = (
        load_sentiment_config(
            env_file=None
        )
    )

    assert (
            config.provider
            == "ollama"
    )

    assert (
            config.model
            == "qwen2.5:7b"
    )

    assert (
            config.base_url
            == "http://127.0.0.1:11434"
    )

    assert (
            config.request_timeout_seconds
            == 180
    )

    assert config.temperature == 0.0

    assert config.max_retries == 2

    assert (
            config.retry_backoff_seconds
            == (3, 8)
    )

    assert (
            config.evidence_max_items
            == 3
    )

    assert (
            config.prompt_version
            == "sentiment_v7"
    )

    assert (
            config.rule_version
            == "sentiment_rules_v5"
    )


def test_sentiment_config_from_environment(
        monkeypatch,
) -> None:
    monkeypatch.setenv(
        "SENTIMENT_MODEL",
        "test-model",
    )

    monkeypatch.setenv(
        "SENTIMENT_REQUEST_TIMEOUT_SECONDS",
        "60",
    )

    monkeypatch.setenv(
        "SENTIMENT_TEMPERATURE",
        "0.2",
    )

    monkeypatch.setenv(
        "SENTIMENT_RETRY_BACKOFF_SECONDS",
        "1,5,10",
    )

    monkeypatch.setenv(
        "SENTIMENT_NEGATIVE_PRIORITY",
        "false",
    )

    config = (
        load_sentiment_config(
            env_file=None
        )
    )

    assert (
            config.model
            == "test-model"
    )

    assert (
            config.request_timeout_seconds
            == 60
    )

    assert (
            config.temperature
            == 0.2
    )

    assert (
            config.retry_backoff_seconds
            == (1, 5, 10)
    )

    assert (
            config.negative_priority
            is False
    )


def test_invalid_sentiment_temperature(
        monkeypatch,
) -> None:
    monkeypatch.setenv(
        "SENTIMENT_TEMPERATURE",
        "9",
    )

    with pytest.raises(
            ConfigurationError,
            match=(
                    "SENTIMENT_TEMPERATURE"
            ),
    ):
        load_sentiment_config(
            env_file=None
        )


def test_invalid_sentiment_provider(
        monkeypatch,
) -> None:
    monkeypatch.setenv(
        "SENTIMENT_PROVIDER",
        "unknown",
    )

    with pytest.raises(
            ConfigurationError,
            match="SENTIMENT_PROVIDER",
    ):
        load_sentiment_config(
            env_file=None
        )
