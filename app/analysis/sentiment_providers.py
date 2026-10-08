import asyncio
import json
import re
import socket
import time

from datetime import (
    datetime,
    timezone,
)
from typing import Protocol
from urllib.error import (
    HTTPError,
    URLError,
)
from urllib.request import (
    Request,
    urlopen,
)

from app.analysis.models import (
    ModelResponse,
)
from app.analysis.sentiment_config import (
    SentimentConfig,
)

RETRYABLE_SENTIMENT_ERROR_TYPES = {
    "rate_limit",
    "transient_api_error",
    "timeout",
    "network_error",
}


class SentimentApiError(RuntimeError):
    """
    Sentiment Provider 标准异常。

    Provider 只负责识别异常类型，
    是否重试由上层 orchestration 决定。
    """

    def __init__(
            self,
            message: str,
            *,
            error_type: str,
            error_code: str | None = None,
            retry_after_seconds: (
                    float | None
            ) = None,
    ) -> None:
        super().__init__(
            message
        )

        self.error_type = error_type
        self.error_code = error_code
        self.retry_after_seconds = (
            retry_after_seconds
        )

    @property
    def retryable(
            self,
    ) -> bool:
        return (
                self.error_type
                in RETRYABLE_SENTIMENT_ERROR_TYPES
        )


class SentimentModelProvider(
    Protocol
):
    provider_name: str
    model_name: str

    async def classify(
            self,
            *,
            system_prompt: str,
            user_prompt: str,
    ) -> ModelResponse:
        ...

    async def health_check(
            self,
    ) -> bool:
        ...


class OllamaSentimentProvider:
    provider_name = "ollama"

    def __init__(
            self,
            config: SentimentConfig,
    ) -> None:
        self.config = config

        self.model_name = (
            config.model
        )

        self.base_url = (
            config.base_url.rstrip("/")
        )

    async def classify(
            self,
            *,
            system_prompt: str,
            user_prompt: str,
    ) -> ModelResponse:
        """
        执行一次 Ollama Sentiment 请求。

        注意：
        此处不做 retry。
        """

        return await asyncio.to_thread(
            self._classify_sync,
            system_prompt,
            user_prompt,
        )

    def _classify_sync(
            self,
            system_prompt: str,
            user_prompt: str,
    ) -> ModelResponse:
        url = (
            f"{self.base_url}/api/chat"
        )

        request_payload = {
            "model": self.model_name,

            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],

            "stream": False,

            "format": "json",

            "options": {
                "temperature": (
                    self.config.temperature
                ),
            },
        }

        body = json.dumps(
            request_payload,
            ensure_ascii=False,
        ).encode("utf-8")

        request = Request(
            url=url,
            data=body,
            headers={
                "Content-Type": (
                    "application/json"
                ),
            },
            method="POST",
        )

        started_at = _utc_now()

        started_perf = (
            time.perf_counter()
        )

        try:
            with urlopen(
                    request,
                    timeout=(
                            self.config
                                    .request_timeout_seconds
                    ),
            ) as response:
                raw_http = (
                    response
                    .read()
                    .decode(
                        "utf-8",
                        errors="replace",
                    )
                )

        except HTTPError as exc:
            raise _http_error(
                exc
            ) from exc

        except (
                socket.timeout,
                TimeoutError,
        ) as exc:
            raise SentimentApiError(
                "Ollama sentiment request timed out",
                error_type="timeout",
            ) from exc

        except URLError as exc:
            reason = getattr(
                exc,
                "reason",
                None,
            )

            if isinstance(
                    reason,
                    (
                            socket.timeout,
                            TimeoutError,
                    ),
            ):
                raise SentimentApiError(
                    "Ollama sentiment request timed out",
                    error_type="timeout",
                ) from exc

            raise SentimentApiError(
                (
                    "Ollama sentiment "
                    f"network error: {exc}"
                ),
                error_type="network_error",
            ) from exc

        except OSError as exc:
            raise SentimentApiError(
                (
                    "Ollama sentiment "
                    f"network error: {exc}"
                ),
                error_type="network_error",
            ) from exc

        latency_seconds = (
                time.perf_counter()
                - started_perf
        )

        finished_at = _utc_now()

        try:
            data = json.loads(
                raw_http
            )

        except json.JSONDecodeError as exc:
            raise SentimentApiError(
                (
                    "Ollama HTTP response "
                    "is not valid JSON"
                ),
                error_type="invalid_response",
            ) from exc

        content = _ollama_content(
            data
        )

        payload = _parse_json_object(
            content
        )

        prompt_tokens = _optional_int(
            data.get(
                "prompt_eval_count"
            )
        )

        completion_tokens = _optional_int(
            data.get(
                "eval_count"
            )
        )

        total_tokens = None

        if (
                prompt_tokens is not None
                or completion_tokens
                is not None
        ):
            total_tokens = (
                    (prompt_tokens or 0)
                    + (completion_tokens or 0)
            )

        return ModelResponse(
            payload=payload,

            latency_seconds=(
                latency_seconds
            ),

            prompt_tokens=(
                prompt_tokens
            ),

            completion_tokens=(
                completion_tokens
            ),

            total_tokens=total_tokens,

            raw_content=content,

            response_json_keys=list(
                payload.keys()
            ),

            request_started_at=(
                started_at
            ),

            request_finished_at=(
                finished_at
            ),
        )

    async def health_check(
            self,
    ) -> bool:
        return await asyncio.to_thread(
            self._health_check_sync
        )

    def _health_check_sync(
            self,
    ) -> bool:
        request = Request(
            url=(
                f"{self.base_url}/api/tags"
            ),
            method="GET",
        )

        try:
            with urlopen(
                    request,
                    timeout=(
                            self.config
                                    .health_check_timeout_seconds
                    ),
            ) as response:
                return (
                        200
                        <= response.getcode()
                        < 300
                )

        except (
                HTTPError,
                URLError,
                socket.timeout,
                TimeoutError,
                OSError,
        ):
            return False


def create_sentiment_provider(
        config: SentimentConfig,
) -> SentimentModelProvider:
    if config.provider == "ollama":
        return OllamaSentimentProvider(
            config
        )

    raise ValueError(
        "Unsupported sentiment provider: "
        f"{config.provider}"
    )


def _ollama_content(
        data: object,
) -> str:
    if not isinstance(
            data,
            dict,
    ):
        raise SentimentApiError(
            (
                "Ollama response root "
                "is not a JSON object"
            ),
            error_type="invalid_response",
        )

    message = data.get(
        "message"
    )

    content = None

    if isinstance(
            message,
            dict,
    ):
        content = message.get(
            "content"
        )

    if not content:
        content = (
                data.get("response")
                or data.get("content")
        )

    if not isinstance(
            content,
            str,
    ):
        raise SentimentApiError(
            (
                "Ollama response does not "
                "contain model content"
            ),
            error_type="invalid_response",
        )

    return content.strip()


def _parse_json_object(
        content: str,
) -> dict:
    text = content.strip()

    fence_match = re.fullmatch(
        (
            r"```(?:json)?\s*"
            r"(.*?)"
            r"\s*```"
        ),
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if fence_match:
        text = (
            fence_match
            .group(1)
            .strip()
        )

    try:
        payload = json.loads(
            text
        )

    except json.JSONDecodeError:
        object_match = re.search(
            r"\{.*\}",
            text,
            flags=re.DOTALL,
        )

        if object_match is None:
            raise SentimentApiError(
                (
                    "Ollama model content "
                    "does not contain JSON object"
                ),
                error_type="invalid_response",
            )

        try:
            payload = json.loads(
                object_match.group(0)
            )

        except json.JSONDecodeError as exc:
            raise SentimentApiError(
                (
                    "Ollama model content "
                    "contains invalid JSON"
                ),
                error_type="invalid_response",
            ) from exc

    if not isinstance(
            payload,
            dict,
    ):
        raise SentimentApiError(
            (
                "Ollama model payload "
                "is not a JSON object"
            ),
            error_type="invalid_response",
        )

    return payload


def _http_error(
        exc: HTTPError,
) -> SentimentApiError:
    status = int(
        exc.code
    )

    retry_after = None

    if exc.headers is not None:
        raw_retry_after = (
            exc.headers.get(
                "Retry-After"
            )
        )

        if raw_retry_after:
            try:
                retry_after = float(
                    raw_retry_after
                )

            except ValueError:
                retry_after = None

    if status == 429:
        error_type = "rate_limit"

    elif status in {
        500,
        502,
        503,
        504,
    }:
        error_type = (
            "transient_api_error"
        )

    else:
        error_type = "api_error"

    return SentimentApiError(
        (
            "Ollama sentiment HTTP error: "
            f"{status}"
        ),
        error_type=error_type,
        error_code=str(status),
        retry_after_seconds=(
            retry_after
        ),
    )


def _optional_int(
        value: object,
) -> int | None:
    if isinstance(
            value,
            bool,
    ):
        return None

    if isinstance(
            value,
            int,
    ):
        return value

    return None


def _utc_now() -> str:
    return (
        datetime.now(
            timezone.utc
        )
        .isoformat()
    )
