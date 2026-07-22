# Enterprise AI Agent

企业级 **AI 软件团队平台**：输入自然语言需求，自动完成 PRD、架构、后端、前端、测试、文档、Git 与部署的端到端交付。

## 仓库说明

| 目录 | 说明 |
|------|------|
| `backend/` | 平台后端（FastAPI）、Software Team 流水线、Dashboard API |
| `frontend/` | Dashboard 前端（Vue3 + Vite + Element Plus） |
| `backend/applications/software_team/` | 多 Agent 软件开发流水线核心 |
| `backend/scripts/run_single_project.py` | 单项目流水线验证脚本 |
| `backend/workspace/library_p0_run13/` | **演示样例**：AI 生成的图书管理系统（可运行） |
| `backend/applications/embodied_demo/` | **Task13 演示**：具身智能 Agent（Vision + Robot + Policy） |

**GitHub 仓库：** https://github.com/123jame/enterprise-ai-agent

**架构图：** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | **演示指南：** [DEMO.md](DEMO.md) | **具身智能 Task13：** [docs/TASK13_EMBODIED.md](docs/TASK13_EMBODIED.md)

## 核心能力

- **多 Agent 协作**：Product → Architect → Backend → Frontend → QA → Documentation
- **自动验证**：结构检查、pytest、前后端执行策略
- **Git 工作流**：feature → develop → main 自动合并
- **Dashboard**：Web 界面提交需求、查看流水线进度
- **可演示交付**：Run13 图书系统后端 API 可现场完成借还书
- **具身智能扩展（Task13）**：Vision / Robot / Observation / Policy，支持 `analyze_image` 与机器人 Tool

## 快速开始

### 1. 环境准备

- Python 3.11+
- Node.js 18+（Dashboard 前端）
- Git
- LLM API（默认 DeepSeek，见 `backend/.env.example`）

```powershell
cd backend
copy .env.example .env
# 编辑 .env，填入 OPENAI_API_KEY、OPENAI_BASE_URL、MODEL_NAME
pip install -r requirements.txt
```

### 2. 启动平台

**终端 A — 平台后端（端口 8001，勿用 --reload）**

```powershell
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

**终端 B — Dashboard 前端**

```powershell
cd frontend
npm install
npm run dev
```

浏览器打开 Vite 提示的地址（通常 `http://localhost:5173`）。

### 3. 运行流水线（命令行）

```powershell
cd backend
python scripts/run_single_project.py
```

成功标志：`RESULT {"success": true, ...}`

### 4. 演示样例：图书管理系统

详见 [DEMO.md](./DEMO.md)。

```powershell
cd backend/workspace/library_p0_run13
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```

- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/api/health

### 5. 具身智能 Demo（Task13）

详见 [docs/TASK13_EMBODIED.md](docs/TASK13_EMBODIED.md)。

```powershell
cd backend
python -m applications.embodied_demo.demo
```

## 流水线架构

详见 **[系统架构图 docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**（含 Mermaid 图，GitHub 可直接渲染）。

```
用户需求
  ↓
EnterpriseCoordinator
  ↓
ProductAgent → ArchitectAgent → BackendAgent → FrontendAgent
  → QAAgent → DocumentationAgent
  ↓
Git (feature → develop → main) + 部署评估
  ↓
backend/workspace/<项目名>/
```

## 演示定位

当前版本适合 **「可演示、可验证的原型交付」**：

- ✅ 平台自动生完整工程产物
- ✅ 后端 API 可真实操作（借书、还书、统计）
- ⚠️ 前端为骨架，生产环境需加权限、UI、运维

## 近期修复（P0）

- ProductAgent PRD 长度限制与 Tool Loop 优化
- Dashboard 阶段映射与 delivery 误报修复
- Git develop/main 分支自动创建
- 前端静态项目识别、Windows npm 路径
- QAAgent pytest 依赖安装与 tests 验证逻辑
- DocumentationAgent README 路径与 pipeline 执行检查

## 许可证

Private / 内部项目（如需开源许可证请自行补充）。
