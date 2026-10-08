from app.core.exceptions import (
    GeoCollectorError,
)


class PipelinePausedError(
        GeoCollectorError
):
    """
    Pipeline 因可恢复条件而暂停。

    例如 DeepSeek RATE_LIMIT。
    此时 checkpoint 已保存，
    后续 Analysis / Package 不应继续执行。
    """

    def __init__(
            self,
            *,
            batch_id: str,
            reason: str,
    ) -> None:
        self.batch_id = batch_id
        self.reason = reason

        super().__init__(
            f"pipeline paused: "
            f"{batch_id}: {reason}"
        )
