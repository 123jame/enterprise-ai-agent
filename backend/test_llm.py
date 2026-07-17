from app.llm.factory import get_llm_client
from app.llm.types import Message
from applications.software_team.tools.registrar import register_team_tools

register_team_tools()
client = get_llm_client()

print("Tool count:", len(client._get_tool_schemas()))
print("Running lightweight connectivity check...")

result = client.chat([
    Message(
        role="user",
        content="你好，请介绍一下自己。"
    )
])

print(result.model)
print((result.content or "")[:500])
print()
print("Tip: run `python scripts/test_llm_project.py` to simulate project load.")