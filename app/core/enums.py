from enum import Enum


class GeoMode(str, Enum):
    """GEO 业务采集模式。"""

    QUICK = "quick"
    EXPERT = "expert"


class TaskStatus(str, Enum):
    """单个采集任务的生命周期状态。"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class ValidationStatus(str, Enum):
    """采集结果的数据质量验证状态。"""

    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
    FAIL = "FAIL"


class ValidationSeverity(str, Enum):
    """单条 Validation Issue 的严重程度。"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class FailureType(str, Enum):
    """采集过程中的标准失败类型。"""

    CAPTCHA = "captcha"
    RISK_CONTROL = "risk_control"
    LOGIN_EXPIRED = "login_expired"

    ANSWER_TIMEOUT = "answer_timeout"
    ANSWER_EMPTY = "answer_empty"
    GENERATION_INTERRUPTED = "generation_interrupted"

    SOURCE_INCOMPLETE = "source_incomplete"

    UI_CHANGED = "ui_changed"
    NETWORK_ERROR = "network_error"
    ACQUISITION_FAILED = "acquisition_failed"
