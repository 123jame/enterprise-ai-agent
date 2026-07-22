from app.tools.registry import ToolRegistry
from app.tools.time_tool import TimeTool
from app.robot.tool_registrar import register_robot_tools
from app.vision.tool_registrar import register_vision_tools


class ToolFactory:
    """
    Tool 工厂
    """

    _initialized = False

    @classmethod
    def initialize(cls) -> None:

        if cls._initialized:

            return

        ToolRegistry.register(

            TimeTool()

        )

        register_vision_tools()

        register_robot_tools()

        cls._initialized = True

    @classmethod
    def get(
        cls,
        name: str
    ):

        cls.initialize()

        return ToolRegistry.get(name)