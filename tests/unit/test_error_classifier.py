from app.core.enums import FailureType
from app.deepseek.error_classifier import (
    classify_failure,
)


def test_timeout_error_maps_to_answer_timeout():
    result = classify_failure(
        TimeoutError(
            "answer timeout"
        )
    )

    assert (
            result
            == FailureType.ANSWER_TIMEOUT
    )


def test_connection_error_maps_to_network_error():
    result = classify_failure(
        ConnectionError(
            "network failed"
        )
    )

    assert (
            result
            == FailureType.NETWORK_ERROR
    )


def test_selector_error_maps_to_ui_changed():
    result = classify_failure(
        Exception(
            "locator not found"
        )
    )

    assert (
            result
            == FailureType.UI_CHANGED
    )


def test_unknown_error_maps_to_default():
    result = classify_failure(
        Exception(
            "unknown error"
        )
    )

    assert (
            result
            == FailureType.ACQUISITION_FAILED
    )
