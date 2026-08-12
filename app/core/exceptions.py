class GeoCollectorError(Exception):
    """GEO 采集系统基础异常"""


class BrowserError(GeoCollectorError):
    """浏览器生命周期或浏览器操作异常"""


class LoginExpiredError(BrowserError):
    """DeepSeek 登录状态失效"""


class CaptchaDetectedError(BrowserError):
    """检测到验证码或人工验证"""


class RiskControlError(BrowserError):
    """检测到平台风控"""


class UiChangedError(BrowserError):
    """页面 DOM 或关键 UI 结构发生变化"""


class NetworkError(GeoCollectorError):
    """采集过程中发生网络异常"""


class AnswerTimeoutError(GeoCollectorError):
    """等待回答完成超时"""


class AnswerEmptyError(GeoCollectorError):
    """未获得有效回答正文"""


class GenerationInterruptedError(GeoCollectorError):
    """回答生成过程异常中断"""


class SourceCollectionError(GeoCollectorError):
    """信源采集过程异常"""


class AcquisitionFailedError(GeoCollectorError):
    """采集任务整体失败"""


class ConfigurationError(GeoCollectorError):
    """项目配置无效或缺失"""


class PackageExportError(GeoCollectorError):
    """GEO Package 导出失败"""
