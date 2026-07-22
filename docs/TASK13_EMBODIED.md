# Task13：Embodied AI Agent Extension

> 在现有 LLM Agent Framework 基础上扩展具身智能能力：Vision、Robot、Observation、Policy 与 Demo。

---

## 1. 总体架构

```
User
 |
Agent
 |
LLM Planner
 |
Agent Loop
 |
-----------------
|       |        |
Vision Robot Policy
Tool   Tool   Model
 |
Environment
 |
Observation
 |
Agent 继续推理
```

---

## 2. 模块说明

| 子任务 | 路径 | 说明 |
|--------|------|------|
| 13.1 Vision Module | `backend/app/vision/` | `BaseVisionProvider`、`MockVisionProvider` |
| 13.2 Vision Tool | `analyze_image` | Vision 接入 ToolRegistry |
| 13.3 Robot Module | `backend/app/robot/` | `BaseRobot`、`MockRobot` |
| 13.4 Robot Tool | `robot_move` / `robot_grasp` / `robot_release` | Robot 接入 ToolRegistry |
| 13.5 Observation | `backend/app/embodied/` | `Observation` 对象与 `ObservationFactory` |
| 13.6 Agent Loop | `backend/app/runtime/agent_executor.py` | `enable_embodied=True` 启用 Action→Observation 循环 |
| 13.7 Policy | `backend/app/policy/` | `BasePolicy`、`MockPolicy` |
| 13.8 Demo | `backend/applications/embodied_demo/` | 端到端演示「拿红色杯子」 |

---

## 3. 快速开始

### 3.1 运行具身智能 Demo（推荐）

```powershell
cd backend
python -m applications.embodied_demo.demo
```

自定义指令：

```powershell
python -m applications.embodied_demo.demo --instruction "帮我拿桌上的红色杯子"
```

**预期流程：**

1. `analyze_image` — 视觉观察，识别 red cup
2. `Policy.predict` — 规划 `robot_move` + `robot_grasp`
3. `robot_move(table)` — 移动到桌面
4. `robot_grasp(red cup)` — 抓取成功
5. Policy 判定任务完成

### 3.2 启用具身 Agent Loop（ChatAgent）

```python
from app.agents.chat_agent import ChatAgent
from app.runtime.config import AgentConfig

agent = ChatAgent(
    config=AgentConfig(
        enable_embodied=True,
        max_iterations=8,
    )
)
```

`enable_embodied=False`（默认）时，行为与原有 Agent Loop 完全一致。

### 3.3 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `VISION_PROVIDER` | `mock` | 视觉 Provider |
| `ROBOT_PROVIDER` | `mock` | 机器人 Provider |
| `POLICY_PROVIDER` | `mock` | 策略 Provider |

---

## 4. 核心接口

### 4.1 Vision

```python
from app.vision import get_vision_provider

result = get_vision_provider().analyze(
    image="mock-scene-image",
    prompt="找桌上的红色杯子",
)
print(result.detected_objects)
```

### 4.2 Robot

```python
from app.robot import get_robot

robot = get_robot()
robot.move("table")
robot.grasp("red cup")
print(robot.get_state())
```

### 4.3 Observation

```python
from app.embodied import ObservationFactory
from app.tools.manager import ToolManager
from app.tools.types import ToolContext

result = ToolManager().execute(
    ToolContext(
        tool_name="analyze_image",
        arguments={"image": "mock", "prompt": "找红色杯子"},
    )
)
observation = ObservationFactory.from_tool_result(
    result,
    tool_name="analyze_image",
)
print(observation.to_prompt_text())
```

### 4.4 Policy

```python
from app.policy import get_policy

prediction = get_policy().predict(
    observation,
    "帮我拿桌上的红色杯子",
)
for action in prediction.actions:
    print(action.name, action.parameters)
```

---

## 5. Tool 列表

| Tool 名称 | 参数 | 说明 |
|-----------|------|------|
| `analyze_image` | `image`, `prompt` | 视觉分析 |
| `robot_move` | `target` 或 `x/y/z` | 机器人移动 |
| `robot_grasp` | `target` | 抓取物体 |
| `robot_release` | 无 | 释放物体 |

Tool 返回的 JSON Observation 格式：

```json
{"type": "vision", "content": "red cup、红色杯子", ...}
{"type": "robot", "content": "grasp success: red cup", ...}
```

---

## 6. 测试

```powershell
cd backend

python -m app.vision.tests.test_vision
python -m app.vision.tests.test_vision_tool
python -m app.robot.tests.test_robot
python -m app.robot.tests.test_robot_tools
python -m app.embodied.tests.test_observation
python -m app.embodied.tests.test_agent_loop
python -m app.policy.tests.test_policy
python -m applications.embodied_demo.tests.test_embodied_demo
```

---

## 7. 扩展指南

所有模块均采用 **抽象接口 + Registry + Factory** 设计，替换真实实现时只需：

1. 实现 `BaseVisionProvider` / `BaseRobot` / `BasePolicy`
2. 在对应 Registry 中 `register(name, cls)`
3. 设置环境变量（如 `VISION_PROVIDER=openai`）

预留扩展：

- Vision：OpenAI Vision、Qwen-VL、LLaVA、CLIP
- Robot：ROS、UR5、真实机械臂 SDK
- Policy：OpenVLA、RT-2、π0

---

## 8. 目录结构

```
backend/app/
├── vision/          # 视觉模块
├── robot/           # 机器人模块
├── embodied/        # Observation + Agent Loop 升级
├── policy/          # 策略接口
└── runtime/         # AgentExecutor（enable_embodied）

backend/applications/
└── embodied_demo/   # Task13.8 演示
```
