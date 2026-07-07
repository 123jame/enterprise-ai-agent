from app.tools.base_tool import BaseTool


class ToolRegistry:
    """
    Tool 注册中心
    """

    _tools: dict[str, BaseTool] = {}

    @classmethod
    def register(
        cls,
        tool: BaseTool
    ) -> None:
        """
        注册 Tool
        """
        cls._tools[tool.name] = tool

    @classmethod
    def get(
        cls,
        name: str
    ) -> BaseTool:
        """
        根据名称获取 Tool
        """
        if name not in cls._tools:
            raise ValueError(f"Tool '{name}' is not registered.")

        return cls._tools[name]

    @classmethod
    def get_all(
        cls
    ) -> list[BaseTool]:
        """
        获取所有 Tool
        """
        return list(cls._tools.values())

    @classmethod
    def get_schemas(
        cls
    ) -> list[dict]:
        """
        获取所有 Tool Schema，供 LLM Tool Calling 使用
        """
        return [
            tool.schema
            for tool in cls._tools.values()
        ]