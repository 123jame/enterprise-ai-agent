DEFAULT_WORKSPACE_DIRS = (
    "backend",
    "frontend",
    "database",
    "docs",
    "tests",
    "output",
    "temp",
)

DEFAULT_TECH_STACK = [
    "Python",
    "FastAPI",
]

DEFAULT_ENCODING = "utf-8"

# 限制注入 LLM 的单次文本长度，避免代理/upstream 因超大请求返回 502
MAX_TOOL_FILE_CHARS = 12_000

MAX_ARTIFACT_FILE_CHARS = 8_000

MAX_PROMPT_MESSAGE_CHARS = 6_000

# ProductAgent 单次 write_file 写入 PRD 的上限，避免 Tool JSON 过大
MAX_PRD_WRITE_CHARS = 3_500