from abc import ABC
from abc import abstractmethod
from typing import Any


class BaseTool(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool 名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool 描述"""
        pass

    @property
    @abstractmethod
    def schema(self) -> dict[str, Any]:
        """
        返回 OpenAI Tool Schema
        """
        pass

    @abstractmethod
    def execute(self, context):
        """
        执行 Tool
        """
        pass