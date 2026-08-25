import asyncio
import json
import socket

from unittest.mock import patch
from urllib.error import (
    HTTPError,
    URLError,
)

import pytest

from app.analysis.models import (
    ModelResponse,
)
from app.analysis.sentiment_config import (
    SentimentConfig,
)
from app.analysis.sentiment_providers import (
    OllamaSentimentProvider,
    SentimentApiError,
    create_sentiment_provider,
)


class FakeResponse:
    def __init__(
            self,
            payload: dict,
            status: int = 200,
    ) -> None:
        self.payload = payload
        self.status = status

    def __enter__(
            self,
    ):
        return self

    def __exit__(
            self,
            exc_type,
            exc,
            traceback,
    ) -> None:
        return None

    def read(
            self,
    ) -> bytes:
        return json.dumps(
            self.payload,
            ensure_ascii=False,
        ).encode("utf-8")

    def getcode(
            self,
    ) -> int:
        return self.status


def _config() -> SentimentConfig:
    return SentimentConfig()


def test_create_ollama_provider() -> None:
    provider = (
        create_sentiment_provider(
            _config()
        )
    )

    assert (
            provider.provider_name
            == "ollama"
    )

    assert (
            provider.model_name
            == "qwen2.5:7b"
    )


def test_ollama_classify() -> None:
    provider = (
        OllamaSentimentProvider(
            _config()
        )
    )

    response_data = {
        "message": {
            "content": json.dumps(
                {
                    "target_name": "鸿茅药酒",
                    "sentiment": "neutral",
                    "reason": "客观事实",
                    "evidence": [],
                    "confidence": 0.8,
                },
                ensure_ascii=False,
            )
        },
        "prompt_eval_count": 100,
        "eval_count": 20,
    }

    with patch(
            (
                    "app.analysis."
                    "sentiment_providers.urlopen"
            ),
            return_value=FakeResponse(
                response_data
            ),
    ):
        result = asyncio.run(
            provider.classify(
                system_prompt="system",
                user_prompt="user",
            )
        )

    assert isinstance(
        result,
        ModelResponse,
    )

    assert (
            result.payload["sentiment"]
            == "neutral"
    )

    assert result.prompt_tokens == 100

    assert (
            result.completion_tokens
            == 20
    )

    assert result.total_tokens == 120


def test_ollama_request_payload() -> None:
    provider = (
        OllamaSentimentProvider(
            _config()
        )
    )

    captured = {}

    def fake_urlopen(
            request,
            timeout,
    ):
        captured["url"] = (
            request.full_url
        )

        captured["timeout"] = timeout

        captured["body"] = (
            json.loads(
                request.data.decode(
                    "utf-8"
                )
            )
        )

        return FakeResponse(
            {
                "message": {
                    "content": (
                        '{"sentiment":"neutral"}'
                    )
                }
            }
        )

    with patch(
            (
                    "app.analysis."
                    "sentiment_providers.urlopen"
            ),
            side_effect=fake_urlopen,
    ):
        asyncio.run(
            provider.classify(
                system_prompt="SYSTEM",
                user_prompt="USER",
            )
        )

    assert (
            captured["url"]
            == (
                "http://127.0.0.1:11434"
                "/api/chat"
            )
    )

    assert (
            captured["timeout"]
            == 180
    )

    body = captured["body"]

    assert (
            body["model"]
            == "qwen2.5:7b"
    )

    assert (
            body["stream"]
            is False
    )

    assert (
            body["format"]
            == "json"
    )

    assert (
            body["options"][
                "temperature"
            ]
            == 0.0
    )


def test_markdown_json_fence_is_supported() -> None:
    provider = (
        OllamaSentimentProvider(
            _config()
        )
    )

    response_data = {
        "message": {
            "content": (
                "```json\n"
                '{"sentiment":"positive"}'
                "\n```"
            )
        }
    }

    with patch(
            (
                    "app.analysis."
                    "sentiment_providers.urlopen"
            ),
            return_value=FakeResponse(
                response_data
            ),
    ):
        result = asyncio.run(
            provider.classify(
                system_prompt="system",
                user_prompt="user",
            )
        )

    assert (
            result.payload["sentiment"]
            == "positive"
    )


def test_rate_limit_error() -> None:
    provider = (
        OllamaSentimentProvider(
            _config()
        )
    )

    error = HTTPError(
        url="http://localhost",
        code=429,
        msg="Too Many Requests",
        hdrs=None,
        fp=None,
    )

    with patch(
            (
                    "app.analysis."
                    "sentiment_providers.urlopen"
            ),
            side_effect=error,
    ):
        with pytest.raises(
                SentimentApiError,
        ) as exc_info:
            asyncio.run(
                provider.classify(
                    system_prompt="system",
                    user_prompt="user",
                )
            )

    assert (
            exc_info.value.error_type
            == "rate_limit"
    )

    assert (
            exc_info.value.retryable
            is True
    )


def test_timeout_error() -> None:
    provider = (
        OllamaSentimentProvider(
            _config()
        )
    )

    with patch(
            (
                    "app.analysis."
                    "sentiment_providers.urlopen"
            ),
            side_effect=socket.timeout(),
    ):
        with pytest.raises(
                SentimentApiError,
        ) as exc_info:
            asyncio.run(
                provider.classify(
                    system_prompt="system",
                    user_prompt="user",
                )
            )

    assert (
            exc_info.value.error_type
            == "timeout"
    )


def test_network_error() -> None:
    provider = (
        OllamaSentimentProvider(
            _config()
        )
    )

    with patch(
            (
                    "app.analysis."
                    "sentiment_providers.urlopen"
            ),
            side_effect=URLError(
                "connection refused"
            ),
    ):
        with pytest.raises(
                SentimentApiError,
        ) as exc_info:
            asyncio.run(
                provider.classify(
                    system_prompt="system",
                    user_prompt="user",
                )
            )

    assert (
            exc_info.value.error_type
            == "network_error"
    )


def test_invalid_model_json() -> None:
    provider = (
        OllamaSentimentProvider(
            _config()
        )
    )

    response_data = {
        "message": {
            "content": (
                "this is not json"
            )
        }
    }

    with patch(
            (
                    "app.analysis."
                    "sentiment_providers.urlopen"
            ),
            return_value=FakeResponse(
                response_data
            ),
    ):
        with pytest.raises(
                SentimentApiError,
        ) as exc_info:
            asyncio.run(
                provider.classify(
                    system_prompt="system",
                    user_prompt="user",
                )
            )

    assert (
            exc_info.value.error_type
            == "invalid_response"
    )
