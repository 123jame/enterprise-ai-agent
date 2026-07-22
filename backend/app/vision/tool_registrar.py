from app.tools.registry import ToolRegistry
from app.vision.vision_tool import AnalyzeImageTool


_vision_tools_registered = False


def register_vision_tools() -> None:
    """
    将 Vision Tool 注册到全局 ToolRegistry。

    与 Software Team 的 registrar 模式一致，避免破坏已有 Tool 接口。
    """

    global _vision_tools_registered

    if _vision_tools_registered:

        return

    ToolRegistry.register(
        AnalyzeImageTool(),
    )

    _vision_tools_registered = True


def reset_vision_tool_registration() -> None:
    """测试辅助：允许重复注册。"""

    global _vision_tools_registered

    _vision_tools_registered = False
