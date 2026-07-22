import json
from typing import Any

from app.tools.base_tool import BaseTool
from app.tools.types import ToolContext
from app.tools.types import ToolResult
from app.vision.base import BaseVisionProvider
from app.vision.exceptions import VisionProviderError
from app.vision.types import VisionAnalysisResult
from app.vision.factory import get_vision_provider


class AnalyzeImageTool(BaseTool):
    """
    图像分析 Tool。

    调用链：Agent -> AnalyzeImageTool -> VisionProvider -> ToolResult(Observation)
    """

    def __init__(
        self,
        vision_provider: BaseVisionProvider | None = None,
    ) -> None:

        self._vision_provider = (
            vision_provider or get_vision_provider()
        )

    @property
    def name(self) -> str:

        return "analyze_image"

    @property
    def description(self) -> str:

        return (
            "Analyze an image using the vision provider. "
            "Use this tool to observe the environment, detect objects, "
            "or answer visual questions before planning robot actions."
        )

    @property
    def schema(self) -> dict[str, Any]:

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image": {
                            "type": "string",
                            "description": (
                                "Image input: file path, base64 string, "
                                "or inline image reference."
                            ),
                        },
                        "prompt": {
                            "type": "string",
                            "description": (
                                "Vision analysis instruction, e.g. "
                                "'find the red cup on the table'."
                            ),
                        },
                    },
                    "required": ["image", "prompt"],
                },
            },
        }

    def execute(
        self,
        context: ToolContext,
    ) -> ToolResult:

        arguments = context.arguments or {}
        image = arguments.get("image")
        prompt = arguments.get("prompt")

        if not image:

            return ToolResult(
                success=False,
                content="Missing required argument: image",
            )

        if not prompt:

            return ToolResult(
                success=False,
                content="Missing required argument: prompt",
            )

        try:

            result = self._vision_provider.analyze(
                image=image,
                prompt=str(prompt),
            )

        except VisionProviderError as error:

            return ToolResult(
                success=False,
                content=str(error),
            )

        observation_content = self._build_observation_content(result)

        return ToolResult(
            success=True,
            content=observation_content,
        )

    def _build_observation_content(
        self,
        result: VisionAnalysisResult,
    ) -> str:
        """
        将视觉分析结果格式化为 Observation 友好内容。

        后续 Observation 模块可直接解析 type=vision 的结构化反馈。
        """

        primary_content = (
            "、".join(result.detected_objects)
            if result.detected_objects
            else result.content
        )

        payload = {
            "type": "vision",
            "content": primary_content,
            "analysis": result.content,
            "detected_objects": result.detected_objects,
            "provider": result.provider,
            "prompt": result.prompt,
            "metadata": result.metadata,
        }

        return json.dumps(
            payload,
            ensure_ascii=False,
        )
