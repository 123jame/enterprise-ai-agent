from app.tools.registry import ToolRegistry
from app.tools.time_tool import TimeTool


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

        cls._initialized = True

    @classmethod
    def get(
        cls,
        name: str
    ):

        cls.initialize()

        return ToolRegistry.get(name)