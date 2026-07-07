# Enterprise AI Agent

企业级 AI Agent 框架，基于 Python + FastAPI 构建，支持 ReAct、Plan-and-Execute、RAG、MCP、可观测性与 Multi-Agent 扩展。

**仓库地址：** https://github.com/123jame/enterprise-ai-agent

---

## 特性

| 模块 | 能力 |
|------|------|
| **Memory** | 会话记忆加载与持久化 |
| **Tool Framework** | 本地 Tool 注册、调用与 Schema 生成 |
| **Agent Loop** | LLM ↔ Tool ReAct 循环 |
| **Agent Runtime** | PromptBuilder、ObservationBuilder、AgentConfig、Tracer |
| **RAG** | Embedding、VectorStore、Retriever、KnowledgeBase |
| **MCP** | MCP Client、Tool Adapter、Server Manager、Resource / Prompt |
| **Planner + Workflow** | Plan-and-Execute、Sequential Workflow、Step 重试 / 跳过 |
| **Observability** | Trace 收集、Metrics、Evaluation、Trace 回放 |
| **Multi-Agent** | Agent 抽象接口、Adapter 适配（Task12 进行中） |

设计原则：**SOLID**、高内聚低耦合、组件可插拔、单 Agent 向后兼容。

---

## 架构概览

```
User Request
    ↓
FastAPI (/api/v1/chat)
    ↓
ChatService → ChatAgent
    ↓
PromptBuilder（System / History / Memory / RAG / MCP / Plan）
    ↓
WorkflowExecutor
    ├─ enable_planner=False → AgentExecutor（ReAct Loop）
    └─ enable_planner=True  → Planner → Workflow → StepExecutor
    ↓
LLMClient ↔ ToolManager（本地 Tool + MCP Tool）
    ↓
AgentResult
    ↓
TraceCollector / Metrics / Evaluation（可选）
```

---

## 项目结构

```
enterprise-ai-agent/
├── README.md
├── .gitignore
└── backend/
    ├── main.py                 # 应用入口
    ├── requirements.txt
    ├── .env.example            # 环境变量模板（复制为 .env 使用）
    └── app/
        ├── agents/             # Agent 实现（ChatAgent、Factory、Registry）
        ├── api/                # FastAPI 路由
        ├── core/               # 配置与日志
        ├── llm/                # LLM 客户端
        ├── memory/             # 记忆管理
        ├── tools/              # Tool 框架
        ├── runtime/            # Agent Runtime（Prompt、Executor、Tracer）
        │   └── plan/           # Planner + Workflow
        ├── rag/                # RAG 检索增强
        ├── mcp/                # MCP 协议集成
        ├── observability/      # Trace / Metrics / Evaluation
        ├── multi_agent/        # Multi-Agent 抽象（Task12）
        ├── services/           # 业务服务层
        ├── schemas/            # Pydantic 模型
        └── prompts/            # System Prompt
```

---

## 快速开始

### 环境要求

- Python 3.11+
- 可用的 OpenAI 兼容 API（OpenAI / 第三方代理均可）

### 1. 克隆仓库

```bash
git clone https://github.com/123jame/enterprise-ai-agent.git
cd enterprise-ai-agent/backend
```

### 2. 创建虚拟环境并安装依赖

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

编辑 `backend/.env`，填入你的 API Key 和模型配置：

```env
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-4o
TEMPERATURE=0.7
MAX_TOKENS=4096
```

> **注意：** `.env` 已被 `.gitignore` 忽略，请勿将 API Key 提交到 Git。

### 4. 启动服务

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 访问

| 地址 | 说明 |
|------|------|
| http://localhost:8000/health | 健康检查 |
| http://localhost:8000/docs | Swagger API 文档 |
| http://localhost:8000/api/v1/chat | 对话接口 |

---

## API 使用

### 对话

**POST** `/api/v1/chat`

```json
{
  "session_id": "user-001",
  "message": "现在几点了？"
}
```

响应：

```json
{
  "success": true,
  "model": "gpt-4o",
  "answer": "当前时间是 ..."
}
```

### 健康检查

**GET** `/health`

```json
{
  "status": "ok",
  "project": "Enterprise AI Agent"
}
```

---

## 配置说明

Runtime 行为通过 `AgentConfig` 控制，可在代码中按需启用：

```python
from app.runtime.config import AgentConfig
from app.agents.chat_agent import ChatAgent

# 默认：ReAct 单 Agent
config = AgentConfig()

# 启用 RAG
config = AgentConfig(enable_rag=True, top_k=3)

# 启用 MCP
config = AgentConfig(enable_mcp=True, mcp_servers=["local-mock"])

# 启用 Plan-and-Execute
config = AgentConfig(enable_planner=True, max_plan_steps=10)

# 启用可观测性
config = AgentConfig(
    enable_trace=True,
    enable_metrics=True,
    enable_evaluation=True,
    exporter_type="console",  # console | json | file | opentelemetry
)

agent = ChatAgent(config=config)
```

主要配置项：

| 配置 | 默认值 | 说明 |
|------|--------|------|
| `max_iterations` | 5 | Agent Loop 最大 Tool 调用轮次 |
| `enable_rag` | False | 启用 RAG 检索 |
| `enable_mcp` | False | 启用 MCP 工具与资源 |
| `enable_planner` | False | 启用 Plan-and-Execute |
| `enable_trace` | False | 启用 Trace 收集 |
| `enable_metrics` | False | 启用执行指标统计 |
| `enable_evaluation` | False | 启用规则评测 |

---

## 代码示例

### 直接调用 Agent

```python
from app.agents.chat_agent import ChatAgent
from app.agents.types import AgentContext
from app.runtime.config import AgentConfig

agent = ChatAgent(config=AgentConfig())
context = AgentContext(
    session_id="demo-session",
    user_message="你好，请介绍一下你自己",
)
result = agent.run(context)
print(result.content)
```

### 回放 Trace（调试）

```python
agent = ChatAgent(config=AgentConfig(enable_trace=True))
result = agent.run(context)

# 查看指标
print(agent.last_metrics)

# 回放执行过程（不重新调用 LLM）
agent.replay_last_trace(verbose=True)
```

### Multi-Agent 接口

```python
from app.multi_agent import Agent, BaseAgentAdapter
from app.agents.chat_agent import ChatAgent

agent = ChatAgent()
assert isinstance(agent, Agent)
print(agent.get_capabilities())  # ['chat', 'tool_calling', ...]
```

---

## 内置 Tool

| Tool | 说明 |
|------|------|
| `get_current_time` | 获取当前时间 |

Tool 通过 `ToolRegistry` 注册，支持扩展本地 Tool 与 MCP Tool。

---

## 开发路线图

- [x] Task 4 — Memory
- [x] Task 5 — Tool Framework
- [x] Task 6 — Agent Loop
- [x] Task 7 — Agent Runtime
- [x] Task 8 — RAG
- [x] Task 9 — MCP
- [x] Task 10 — Planner + Workflow
- [x] Task 11 — Tracing + Evaluation
- [ ] Task 12 — Multi-Agent Runtime（进行中）

---

## 技术栈

- **Web 框架：** FastAPI + Uvicorn
- **LLM：** OpenAI SDK（兼容 OpenAI API 的服务均可）
- **配置：** Pydantic Settings + python-dotenv
- **协议：** MCP（Model Context Protocol）

---

## 许可证

本项目仅供学习与内部开发使用。如需开源许可证，请自行添加 `LICENSE` 文件。
