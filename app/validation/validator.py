from app.core.enums import (
    GeoMode,
    SourceCollectionStatus,
    TaskStatus,
    ValidationSeverity,
    ValidationStatus,
)
from app.core.models import (
    GeoRunResult,
    ValidationIssue,
    ValidationResult,
)


def validate_run_result(
        result: GeoRunResult,
) -> ValidationResult:
    """
    校验单次 GEO 采集结果是否可作为有效样本使用。
    """

    issues: list[ValidationIssue] = []

    if result.status != TaskStatus.SUCCESS:
        issues.append(
            ValidationIssue(
                code="TASK_FAILED",
                message=(
                    "Collection task did not "
                    "finish successfully."
                ),
                severity=(
                    ValidationSeverity.ERROR
                ),
            )
        )

        return ValidationResult(
            status=ValidationStatus.FAIL,
            issues=issues,
            is_complete=False,
        )

    if not result.answer_text_clean.strip():
        issues.append(
            ValidationIssue(
                code="ANSWER_EMPTY",
                message=(
                    "Collected answer text is empty."
                ),
                severity=(
                    ValidationSeverity.ERROR
                ),
            )
        )

        return ValidationResult(
            status=ValidationStatus.FAIL,
            issues=issues,
            is_complete=False,
        )

    source_status = (
        result.sources.status
    )

    if (
            result.task.mode == GeoMode.QUICK
            and source_status
            == SourceCollectionStatus.PARTIAL
    ):
        issues.append(
            ValidationIssue(
                code="SOURCE_PARTIAL",
                message=(
                    "Quick mode source collection "
                    "was only partially complete."
                ),
                severity=(
                    ValidationSeverity.WARNING
                ),
            )
        )

    elif (
            result.task.mode == GeoMode.QUICK
            and source_status
            == SourceCollectionStatus.FAILED
    ):
        issues.append(
            ValidationIssue(
                code="SOURCE_COLLECTION_FAILED",
                message=(
                    "Quick mode source collection "
                    "failed."
                ),
                severity=(
                    ValidationSeverity.WARNING
                ),
            )
        )

    elif (
            result.task.mode == GeoMode.QUICK
            and source_status
            in {
                SourceCollectionStatus.NOT_APPLICABLE,
                SourceCollectionStatus.NOT_SUPPORTED,
            }
    ):
        issues.append(
            ValidationIssue(
                code="SOURCE_UNAVAILABLE",
                message=(
                    "Quick mode did not provide "
                    "source collection capability."
                ),
                severity=(
                    ValidationSeverity.WARNING
                ),
            )
        )

    has_warnings = any(
        issue.severity
        == ValidationSeverity.WARNING
        for issue in issues
    )

    return ValidationResult(
        status=(
            ValidationStatus.PASS_WITH_WARNINGS
            if has_warnings
            else ValidationStatus.PASS
        ),
        issues=issues,
        is_complete=True,
    )
