from app.core.enums import (
    FailureType,
    GeoMode,
    SourceCollectionStatus,
    TaskStatus,
    ValidationStatus,
)
from app.core.models import (
    GeoRunResult,
    SourceCollection,
    ValidationResult,
)


def map_task_status(status: TaskStatus) -> str:
    """映射为 geo_package_v1 task_status。"""

    if status in {
        TaskStatus.SUCCESS,
        TaskStatus.FAILED,
        TaskStatus.RUNNING,
    }:
        return status.value

    return "failed"


def map_validation_status(
    validation: ValidationResult | None,
) -> str:
    """映射为 geo_package_v1 validation_status。"""

    if validation is None:
        return "NOT_APPLICABLE"

    if validation.status in {
        ValidationStatus.PASS,
        ValidationStatus.PASS_WITH_WARNINGS,
        ValidationStatus.FAIL,
    }:
        return validation.status.value

    return "NOT_APPLICABLE"


def map_acquisition_status(
    result: GeoRunResult,
) -> str:
    """映射采集状态。"""

    if result.status == TaskStatus.SUCCESS:
        return "success"

    if (
        result.failure is not None
        and result.failure.type
        in {
            FailureType.CAPTCHA,
            FailureType.RISK_CONTROL,
        }
    ):
        return "risk_control"

    return "failed"


def answer_is_complete(
    result: GeoRunResult,
) -> bool:
    """判断回答是否完整有效。"""

    return bool(
        result.status == TaskStatus.SUCCESS
        and result.answer_text.strip()
        and map_validation_status(
            result.validation
        )
        in {
            "PASS",
            "PASS_WITH_WARNINGS",
        }
    )


def map_source_status(
    mode: GeoMode,
    sources: SourceCollection,
) -> str:
    """映射信源采集状态。"""

    if mode == GeoMode.QUICK:
        return "not_supported"

    mapping = {
        SourceCollectionStatus.SUCCESS: "success",
        SourceCollectionStatus.PARTIAL: "partial_success",
        SourceCollectionStatus.FAILED: "failed",
        SourceCollectionStatus.NOT_APPLICABLE: "not_supported",
        SourceCollectionStatus.NOT_SUPPORTED: "not_supported",
    }

    return mapping.get(
        sources.status,
        "failed",
    )