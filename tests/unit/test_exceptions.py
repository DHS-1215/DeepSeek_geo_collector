import pytest
from app.core.exceptions import (
    AnswerTimeoutError,
    CaptchaDetectedError,
    GeoCollectorError,
    LoginExpiredError,
)


def test_custom_exceptions_inherit_from_geo_collector_error() -> None:
    assert issubclass(AnswerTimeoutError, GeoCollectorError)
    assert issubclass(CaptchaDetectedError, GeoCollectorError)
    assert issubclass(LoginExpiredError, GeoCollectorError)


def test_custom_exception_can_be_raised_and_and_caught() -> None:
    with pytest.raises(AnswerTimeoutError, match="timed out"):
        raise AnswerTimeoutError("answer timed out")
