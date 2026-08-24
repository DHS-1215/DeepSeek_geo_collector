from app.core.enums import FailureType


def classify_failure(
        exc: Exception,
) -> FailureType:
    """
    根据异常类型判断标准失败类型。
    """

    message = str(exc).lower()

    if isinstance(
            exc,
            TimeoutError,
    ):
        return FailureType.ANSWER_TIMEOUT

    if isinstance(
            exc,
            ConnectionError,
    ):
        return FailureType.NETWORK_ERROR

    if (
            "timeout" in message
            or "timed out" in message
    ):
        return FailureType.ANSWER_TIMEOUT

    if (
            "locator" in message
            or "selector" in message
            or "element" in message
            or "not found" in message
    ):
        return FailureType.UI_CHANGED

    return FailureType.ACQUISITION_FAILED


def is_retryable_failure(
        failure_type: FailureType,
) -> bool:
    """
    判断指定失败类型是否适合自动重试。
    """

    return failure_type in {
        FailureType.NETWORK_ERROR,
        FailureType.ANSWER_TIMEOUT,
    }
