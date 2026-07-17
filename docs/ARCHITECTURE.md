# Enterprise AI Agent — 系统架构图

> 企业级 AI 软件团队平台：从自然语言需求到可运行项目产物的端到端交付。

---

## 1. 总体架构

```mermaid
flowchart TB
    subgraph User["用户层"]
        U1[Dashboard 浏览器<br/>Vue3 + Vite]
        U2[CLI 脚本<br/>run_single_project.py]
    end

    subgraph Platform["平台层 backend/app + applications/platform"]
        EC[EnterpriseCoordinator<br/>企业协调器]
        GM[Governance / Config<br/>治理与配置]
        PR[ProjectRegistry<br/>项目注册]
    end

    subgraph Dashboard["Dashboard 层 applications/dashboard"]
        DS[DashboardService]
        RS[RunService]
        EB[EventBus / WebSocket]
    end

    subgraph Team["Software Team 层 applications/software_team"]
        STC[SoftwareTeamCoordinator]
        PL[Pipeline<br/>流水线编排]
        VM[VerificationManager<br/>验证]
        EM[ExecutionManager<br/>执行]
        GS[GitService<br/>Git 工作流]
        DS2[DeploymentService<br/>部署评估]
    end

    subgraph Agents["多 Agent 协作"]
        A1[ProductAgent]
        A2[ArchitectAgent]
        A3[BackendAgent]
        A4[FrontendAgent]
        A5[QAAgent]
        A6[DocumentationAgent]
    end

    subgraph Runtime["运行时"]
        LLM[LLM API<br/>DeepSeek / OpenAI 兼容]
        TM[ToolManager<br/>write_file / read_file]
        MM[MemoryManager]
    end

    subgraph Output["产物 workspace/"]
        WS[docs/ PRD + Architecture]
        BE[backend/ FastAPI]
        FE[frontend/ 静态/Vue]
        TS[tests/ pytest]
        GIT[.git feature→develop→main]
    end

    U1 --> DS
    U2 --> EC
    DS --> RS --> EC
    EC --> GM
    EC --> PR
    EC --> STC
    STC --> PL
    PL --> Agents
    Agents --> LLM
    Agents --> TM
    PL --> VM
    PL --> EM
    PL --> GS
    PL --> DS2
    TM --> Output
    GS --> GIT
    EB -.-> U1
```

---

## 2. Agent 流水线

```mermaid
flowchart LR
    REQ[用户需求] --> P1

    subgraph Pipeline["固定流水线顺序"]
        P1[ProductAgent<br/>docs/PRD.md]
        P2[ArchitectAgent<br/>docs/Architecture.md]
        P3[BackendAgent<br/>backend/]
        P4[FrontendAgent<br/>frontend/]
        P5[QAAgent<br/>tests/]
        P6[DocumentationAgent<br/>README.md]
    end

    P1 --> P2 --> P3 --> P4 --> P5 --> P6

    P6 --> V{VerificationManager<br/>结构 / pytest / 文档}
    V -->|失败| R[RetryPolicy<br/>最多 3 次]
    R --> Pipeline
    V -->|通过| G[GitService<br/>merge to develop]
    G --> M[merge develop → main]
    M --> D[Deployment 健康检查]
    D --> DONE[交付完成]
```

---

## 3. 单 Agent 步骤内部流程

```mermaid
sequenceDiagram
    participant PL as Pipeline
    participant GS as GitService
    participant AG as Agent
    participant LLM as LLM API
    participant TL as Tools
    participant VM as VerificationManager
    participant AM as ArtifactManager

    PL->>GS: begin_agent_step() 创建 feature 分支
    PL->>AG: run(context)
    loop Agent Loop max 16
        AG->>LLM: Think
        LLM-->>AG: tool_calls / answer
        AG->>TL: write_file / read_file
        TL-->>AG: observation
    end
    AG->>AM: 保存产物 Artifact
    PL->>GS: commit_agent_step()
    PL->>VM: verify(target)
    alt 验证失败
        VM-->>PL: failed
        PL->>AG: fix_instruction 重试
    else 验证通过
        VM-->>PL: success
        PL->>GS: merge_agent_to_develop()
    end
```

---

## 4. Git 分支策略

```mermaid
gitGraph
    commit id: "init"
    branch develop
    checkout develop
    branch feature/product-prd
    checkout feature/product-prd
    commit id: "PRD"
    checkout develop
    merge feature/product-prd
    branch feature/backend
    checkout feature/backend
    commit id: "backend"
    checkout develop
    merge feature/backend
    branch feature/qa-tests
    checkout feature/qa-tests
    commit id: "tests"
    checkout develop
    merge feature/qa-tests
    checkout main
    merge develop id: "release"
```

每个 Agent 对应一条 `feature/<项目名>-<角色>` 分支，完成后合并到 `develop`；流水线结束时 `develop → main`。

---

## 5. 验证与执行

```mermaid
flowchart TB
    subgraph Verify["VerificationManager"]
        S1[结构检查<br/>main.py / index.html / test_*.py]
        S2[ExecutionManager<br/>pip / npm / uvicorn 策略]
        S3[pytest<br/>安装依赖 + 运行测试]
        S4[文档检查<br/>PRD / README 非空]
    end

    subgraph Targets["验证目标"]
        T1[docs/PRD.md]
        T2[backend]
        T3[frontend]
        T4[tests]
        T5[README.md]
    end

    T1 --> S4
    T2 --> S1
    T2 --> S2
    T3 --> S1
    T3 --> S2
    T4 --> S1
    T4 --> S3
    T5 --> S4
```

---

## 6. Demo 部署视图（Run13 图书系统）

```mermaid
flowchart LR
    subgraph Demo["本地演示"]
        B[uvicorn backend.main:app<br/>:8000]
        F[python -m http.server<br/>:5173]
        DB[(SQLite<br/>library.db)]
    end

    SW[Swagger /docs] --> B
    FE[index.html] --> F
    F -->|fetch API| B
    B --> DB

    subgraph API["核心 API"]
        API1[/api/books]
        API2[/api/readers]
        API3[/api/borrowings]
        API4[/api/stats]
    end

    B --> API
```

演示路径：`backend/workspace/library_p0_run13/`  
操作指南：见根目录 [DEMO.md](../DEMO.md)

---

## 7. 技术栈

| 层级 | 技术 |
|------|------|
| 平台后端 | Python 3.11+, FastAPI, Pydantic Settings |
| LLM | OpenAI 兼容 API（DeepSeek 等） |
| Dashboard | Vue 3, Vite, Element Plus, Pinia |
| 生成物后端 | FastAPI, SQLAlchemy 2, SQLite |
| 测试 | pytest, httpx |
| 版本控制 | Git（feature / develop / main） |

---

## 8. 关键目录

```
enterprise-ai-agent/
├── backend/
│   ├── app/                          # 平台 FastAPI 入口
│   ├── applications/
│   │   ├── platform/                 # EnterpriseCoordinator
│   │   ├── dashboard/                # Dashboard 服务
│   │   └── software_team/            # 流水线核心
│   ├── scripts/run_single_project.py
│   └── workspace/library_p0_run13/   # Demo 样例
├── frontend/                         # Dashboard UI
├── docs/ARCHITECTURE.md              # 本文档
├── README.md
└── DEMO.md
```
