from app.llm.factory import get_llm_client
from app.llm.types import Message

client = get_llm_client()

result = client.chat([
    Message(
        role="user",
        content="你好，请介绍一下自己。"
    )
])

print(result.model)
print(result.content)