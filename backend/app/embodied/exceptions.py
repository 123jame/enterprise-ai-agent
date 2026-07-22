class EmbodiedError(Exception):
    """具身智能模块基础异常。"""


class ObservationParseError(EmbodiedError):
    """Observation 解析失败。"""

    def __init__(
        self,
        message: str,
        *,
        raw_content: str | None = None,
    ) -> None:

        super().__init__(message)

        self.raw_content = raw_content
