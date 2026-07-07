from datetime import datetime

from app.tools.base_tool import BaseTool
from app.tools.types import ToolContext
from app.tools.types import ToolResult


class TimeTool(BaseTool):

    @property
    def name(self) -> str:
        return "time"

    @property
    def description(self) -> str:
        return "Get current date and time."

    @property
    def schema(self):

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        }

    def execute(
        self,
        context: ToolContext
    ) -> ToolResult:

        now = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        return ToolResult(
            success=True,
            content=now
        )