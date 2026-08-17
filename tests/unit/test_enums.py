from app.core.enums import (
    FailureType,
    GeoMode,
    TaskStatus,
    ValidationSeverity,
    ValidationStatus,
    SourceCollectionStatus,
)


def test_geo_mode_values() -> None:
    assert GeoMode.QUICK.value == "quick"
    assert GeoMode.EXPERT.value == "expert"


def test_task_status_values() -> None:
    assert TaskStatus.PENDING.value == "pending"
    assert TaskStatus.RUNNING.value == "running"
    assert TaskStatus.SUCCESS.value == "success"
    assert TaskStatus.FAILED.value == "failed"


def test_validation_status_values() -> None:
    assert ValidationStatus.PASS.value == "PASS"
    assert ValidationStatus.FAIL.value == "FAIL"
    assert ValidationStatus.PASS_WITH_WARNINGS == "PASS_WITH_WARNINGS"


def test_validation_severity_values() -> None:
    assert ValidationSeverity.INFO.value == 'info'
    assert ValidationSeverity.WARNING.value == 'warning'
    assert ValidationSeverity.ERROR.value == 'error'


def test_failure_type_values() -> None:
    assert FailureType.CAPTCHA.value == "captcha"
    assert FailureType.RISK_CONTROL.value == "risk_control"
    assert FailureType.ANSWER_TIMEOUT.value == "answer_timeout"
    assert FailureType.SOURCE_INCOMPLETE.value == "source_incomplete"
    assert FailureType.UI_CHANGED.value == "ui_changed"


def test_source_collection_status_values() -> None:
    assert SourceCollectionStatus.SUCCESS.value == "success"
    assert SourceCollectionStatus.PARTIAL.value == "partial"
    assert SourceCollectionStatus.FAILED.value == "failed"
    assert SourceCollectionStatus.NOT_APPLICABLE.value == "not_applicable"
    assert SourceCollectionStatus.NOT_SUPPORTED.value == "not_supported"
