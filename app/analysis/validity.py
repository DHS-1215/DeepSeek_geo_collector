from app.core.enums import (
    TaskStatus,
    ValidationStatus,
)
from app.core.models import GeoRunResult


def is_valid_analysis_answer(
        result: GeoRunResult,
) -> bool:
    """
    判断采集结果是否可以进入 GEO Analysis。

    Analysis 通用有效样本口径：
    - task 成功
    - answer_text_clean 非空
    - validation 存在
    - validation 为 PASS / PASS_WITH_WARNINGS
    """

    if result.status != TaskStatus.SUCCESS:
        return False

    if not result.answer_text_clean.strip():
        return False

    if result.validation is None:
        return False

    return (
            result.validation.status
            in {
                ValidationStatus.PASS,
                ValidationStatus.PASS_WITH_WARNINGS,
            }
    )
