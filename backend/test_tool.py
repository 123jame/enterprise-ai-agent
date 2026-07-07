from app.tools.time_tool import TimeTool
from app.tools.types import ToolContext

tool = TimeTool()

context = ToolContext(
    tool_name="time",
    arguments={}
)

result = tool.execute(context)

print(result)
print(result.content)