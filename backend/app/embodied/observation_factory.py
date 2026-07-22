import json
from typing import Any

from app.embodied.exceptions import ObservationParseError
from app.embodied.types import Observation
from app.embodied.types import ObservationType
from app.tools.types import ToolResult


class ObservationFactory:
    """
    Observation 工厂。

    负责将 ToolResult、JSON 字符串或字典转换为统一 Observation 对象。
    """

    @classmethod
    def from_tool_result(
        cls,
        tool_result: ToolResult,
        *,
        tool_name: str | None = None,
    ) -> Observation:
        """
        从 Tool 执行结果构建 Observation。

        若 content 为具身智能 JSON（type=vision/robot），则解析结构化字段；
        否则退化为普通 tool/error Observation。
        """

        if not tool_result.success:

            return Observation(
                type=ObservationType.ERROR.value,
                content=tool_result.content,
                success=False,
                source=tool_name,
            )

        parsed = cls._try_parse_json(tool_result.content)

        if parsed is not None:

            return cls.from_payload(
                parsed,
                source=tool_name,
            )

        return Observation(
            type=ObservationType.TOOL.value,
            content=tool_result.content,
            success=True,
            source=tool_name,
        )

    @classmethod
    def from_json(
        cls,
        content: str,
        *,
        source: str | None = None,
    ) -> Observation:
        """从 JSON 字符串构建 Observation。"""

        parsed = cls._try_parse_json(content)

        if parsed is None:

            raise ObservationParseError(
                "Observation JSON 解析失败",
                raw_content=content,
            )

        return cls.from_payload(
            parsed,
            source=source,
        )

    @classmethod
    def from_payload(
        cls,
        payload: dict[str, Any],
        *,
        source: str | None = None,
    ) -> Observation:
        """
        从字典构建 Observation。

        支持 vision / robot 具身反馈及通用结构。
        """

        observation_type = str(
            payload.get("type", ObservationType.GENERIC.value)
        ).strip()

        content = cls._extract_content(payload)

        if not content:

            raise ObservationParseError(
                "Observation content 不能为空",
                raw_content=json.dumps(
                    payload,
                    ensure_ascii=False,
                ),
            )

        metadata = cls._extract_metadata(payload)

        return Observation(
            type=observation_type,
            content=content,
            success=bool(payload.get("success", True)),
            source=source or payload.get("source"),
            metadata=metadata,
            raw=payload,
        )

    @classmethod
    def vision(
        cls,
        content: str,
        *,
        source: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Observation:
        """快速构建视觉 Observation。"""

        return Observation(
            type=ObservationType.VISION.value,
            content=content,
            success=True,
            source=source,
            metadata=metadata or {},
        )

    @classmethod
    def robot(
        cls,
        content: str,
        *,
        success: bool = True,
        source: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Observation:
        """快速构建机器人 Observation。"""

        return Observation(
            type=ObservationType.ROBOT.value,
            content=content,
            success=success,
            source=source,
            metadata=metadata or {},
        )

    @classmethod
    def _try_parse_json(
        cls,
        content: str,
    ) -> dict[str, Any] | None:

        text = (content or "").strip()

        if not text.startswith("{"):

            return None

        try:

            parsed = json.loads(text)

        except json.JSONDecodeError:

            return None

        if not isinstance(parsed, dict):

            return None

        return parsed

    @classmethod
    def _extract_content(
        cls,
        payload: dict[str, Any],
    ) -> str:

        content = payload.get("content")

        if content is None:

            return ""

        return str(content).strip()

    @classmethod
    def _extract_metadata(
        cls,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        提取除核心字段外的附加信息。

        vision: analysis / detected_objects
        robot: action / state
        """

        reserved_keys = {
            "type",
            "content",
            "success",
            "source",
        }

        metadata = {
            key: value
            for key, value in payload.items()
            if key not in reserved_keys
        }

        return metadata
