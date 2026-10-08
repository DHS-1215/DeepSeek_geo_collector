import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from app.core.config import PROJECT_ROOT
from app.core.exceptions import ConfigurationError


@dataclass(
    frozen=True,
    slots=True,
)
class SentimentConfig:
    """
    GEO Sentiment 模型配置。

    默认参数与豆包 Sentiment 保持一致。
    """

    provider: str = "ollama"

    model: str = "qwen2.5:7b"

    base_url: str = (
        "http://127.0.0.1:11434"
    )

    prompt_version: str = (
        "sentiment_v7"
    )

    rule_version: str = (
        "sentiment_rules_v5"
    )

    model_config_version: str = (
        "sentiment_model_config_v1"
    )

    request_timeout_seconds: int = 180

    health_check_timeout_seconds: int = 3

    temperature: float = 0.0

    max_tokens: int = 256

    max_retries: int = 2

    retry_backoff_seconds: tuple[
        int,
        ...,
    ] = (3, 8)

    max_concurrency: int = 1

    evidence_max_items: int = 3

    context_sentences_before: int = 2

    context_sentences_after: int = 2

    negative_priority: bool = True


def load_sentiment_config(
        env_file: Path | None = (
                PROJECT_ROOT / ".env"
        ),
) -> SentimentConfig:
    """
    从项目统一 .env 中读取 Sentiment 配置。
    """

    if env_file is not None:
        load_dotenv(
            env_file,
            override=False,
        )

    config = SentimentConfig(
        provider=os.getenv(
            "SENTIMENT_PROVIDER",
            "ollama",
        ).strip().lower(),

        model=os.getenv(
            "SENTIMENT_MODEL",
            "qwen2.5:7b",
        ).strip(),

        base_url=os.getenv(
            "SENTIMENT_BASE_URL",
            "http://127.0.0.1:11434",
        ).strip(),

        prompt_version=os.getenv(
            "SENTIMENT_PROMPT_VERSION",
            "sentiment_v7",
        ).strip(),

        rule_version=os.getenv(
            "SENTIMENT_RULE_VERSION",
            "sentiment_rules_v5",
        ).strip(),

        model_config_version=os.getenv(
            "SENTIMENT_MODEL_CONFIG_VERSION",
            "sentiment_model_config_v1",
        ).strip(),

        request_timeout_seconds=(
            _get_int_env(
                "SENTIMENT_REQUEST_TIMEOUT_SECONDS",
                180,
            )
        ),

        health_check_timeout_seconds=(
            _get_int_env(
                "SENTIMENT_HEALTH_CHECK_TIMEOUT_SECONDS",
                3,
            )
        ),

        temperature=_get_float_env(
            "SENTIMENT_TEMPERATURE",
            0.0,
        ),

        max_tokens=_get_int_env(
            "SENTIMENT_MAX_TOKENS",
            256,
        ),

        max_retries=_get_int_env(
            "SENTIMENT_MAX_RETRIES",
            2,
        ),

        retry_backoff_seconds=(
            _get_int_tuple_env(
                "SENTIMENT_RETRY_BACKOFF_SECONDS",
                (3, 8),
            )
        ),

        max_concurrency=_get_int_env(
            "SENTIMENT_MAX_CONCURRENCY",
            1,
        ),

        evidence_max_items=_get_int_env(
            "SENTIMENT_EVIDENCE_MAX_ITEMS",
            3,
        ),

        context_sentences_before=(
            _get_int_env(
                "SENTIMENT_CONTEXT_SENTENCES_BEFORE",
                2,
            )
        ),

        context_sentences_after=(
            _get_int_env(
                "SENTIMENT_CONTEXT_SENTENCES_AFTER",
                2,
            )
        ),

        negative_priority=_get_bool_env(
            "SENTIMENT_NEGATIVE_PRIORITY",
            True,
        ),
    )

    _validate_config(
        config
    )

    return config


def _get_int_env(
        name: str,
        default: int,
) -> int:
    raw = os.getenv(name)

    if raw is None:
        return default

    try:
        return int(raw)

    except ValueError as exc:
        raise ConfigurationError(
            "Invalid integer environment variable: "
            f"{name}={raw!r}"
        ) from exc


def _get_float_env(
        name: str,
        default: float,
) -> float:
    raw = os.getenv(name)

    if raw is None:
        return default

    try:
        return float(raw)

    except ValueError as exc:
        raise ConfigurationError(
            "Invalid float environment variable: "
            f"{name}={raw!r}"
        ) from exc


def _get_bool_env(
        name: str,
        default: bool,
) -> bool:
    raw = os.getenv(name)

    if raw is None:
        return default

    normalized = (
        raw.strip().lower()
    )

    if normalized in {
        "1",
        "true",
        "yes",
        "on",
    }:
        return True

    if normalized in {
        "0",
        "false",
        "no",
        "off",
    }:
        return False

    raise ConfigurationError(
        "Invalid boolean environment variable: "
        f"{name}={raw!r}"
    )


def _get_int_tuple_env(
        name: str,
        default: tuple[int, ...],
) -> tuple[int, ...]:
    raw = os.getenv(name)

    if raw is None:
        return default

    try:
        return tuple(
            int(item.strip())
            for item in raw.split(",")
            if item.strip()
        )

    except ValueError as exc:
        raise ConfigurationError(
            "Invalid integer list environment variable: "
            f"{name}={raw!r}"
        ) from exc


def _validate_config(
        config: SentimentConfig,
) -> None:
    if config.provider != "ollama":
        raise ConfigurationError(
            "SENTIMENT_PROVIDER currently "
            "supports only 'ollama'"
        )

    if not config.model:
        raise ConfigurationError(
            "SENTIMENT_MODEL cannot be empty"
        )

    if not config.base_url:
        raise ConfigurationError(
            "SENTIMENT_BASE_URL cannot be empty"
        )

    if (
            config.request_timeout_seconds
            <= 0
    ):
        raise ConfigurationError(
            "SENTIMENT_REQUEST_TIMEOUT_SECONDS "
            "must be greater than 0"
        )

    if (
            config.health_check_timeout_seconds
            <= 0
    ):
        raise ConfigurationError(
            "SENTIMENT_HEALTH_CHECK_TIMEOUT_SECONDS "
            "must be greater than 0"
        )

    if not (
            0.0
            <= config.temperature
            <= 2.0
    ):
        raise ConfigurationError(
            "SENTIMENT_TEMPERATURE "
            "must be between 0 and 2"
        )

    if config.max_tokens <= 0:
        raise ConfigurationError(
            "SENTIMENT_MAX_TOKENS "
            "must be greater than 0"
        )

    if config.max_retries < 0:
        raise ConfigurationError(
            "SENTIMENT_MAX_RETRIES "
            "must be greater than or equal to 0"
        )

    if config.max_concurrency <= 0:
        raise ConfigurationError(
            "SENTIMENT_MAX_CONCURRENCY "
            "must be greater than 0"
        )

    if config.evidence_max_items < 0:
        raise ConfigurationError(
            "SENTIMENT_EVIDENCE_MAX_ITEMS "
            "must be greater than or equal to 0"
        )

    if (
            config.context_sentences_before
            < 0
    ):
        raise ConfigurationError(
            "SENTIMENT_CONTEXT_SENTENCES_BEFORE "
            "must be greater than or equal to 0"
        )

    if (
            config.context_sentences_after
            < 0
    ):
        raise ConfigurationError(
            "SENTIMENT_CONTEXT_SENTENCES_AFTER "
            "must be greater than or equal to 0"
        )

    if any(
            delay < 0
            for delay
            in config.retry_backoff_seconds
    ):
        raise ConfigurationError(
            "SENTIMENT_RETRY_BACKOFF_SECONDS "
            "cannot contain negative values"
        )
