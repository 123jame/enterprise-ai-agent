from __future__ import annotations

from app.embodied.observation_factory import ObservationFactory
from app.policy.factory import get_policy
from app.robot.factory import get_robot
from app.robot.factory import reset_robot
from app.robot.tool_registrar import reset_robot_tool_registration
from app.tools.factory import ToolFactory
from app.tools.manager import ToolManager
from app.tools.types import ToolContext
from app.vision.tool_registrar import reset_vision_tool_registration

from applications.embodied_demo.types import EmbodiedDemoResult
from applications.embodied_demo.types import EmbodiedDemoStep


class EmbodiedDemoAgent:
    """
    具身智能 Demo Agent。

    完整演示流程：
        用户指令
          ↓
        VisionTool（观察环境）
          ↓
        Observation
          ↓
        Policy（规划动作）
          ↓
        RobotTool（执行 move / grasp / release）
          ↓
        Observation
          ↓
        任务完成
    """

    DEFAULT_IMAGE = "mock-scene-image"
    DEFAULT_VISION_PROMPT = "观察桌面并找到目标物体"

    def __init__(
        self,
        tool_manager: ToolManager | None = None,
    ) -> None:

        ToolFactory._initialized = False
        reset_robot()
        reset_robot_tool_registration()
        reset_vision_tool_registration()
        ToolFactory.initialize()

        self._tool_manager = tool_manager or ToolManager()
        self._policy = get_policy()
        self._robot = get_robot()

    def run(
        self,
        instruction: str,
    ) -> EmbodiedDemoResult:

        normalized_instruction = (instruction or "").strip()

        if not normalized_instruction:

            return EmbodiedDemoResult(
                instruction="",
                success=False,
                content="指令不能为空",
            )

        steps: list[EmbodiedDemoStep] = []
        observations = []

        vision_step = self._run_vision_step(
            normalized_instruction,
        )

        steps.append(vision_step)

        if not vision_step.success or vision_step.observation is None:

            return EmbodiedDemoResult(
                instruction=normalized_instruction,
                success=False,
                content="视觉观察失败，无法继续任务。",
                steps=steps,
            )

        observations.append(vision_step.observation)

        prediction = self._policy.predict(
            vision_step.observation,
            normalized_instruction,
        )

        steps.append(
            EmbodiedDemoStep(
                phase="plan",
                description="Policy 根据 Observation 规划下一步动作",
                policy_prediction=prediction,
                success=True,
                detail=prediction.reasoning,
            )
        )

        if prediction.completed:

            return EmbodiedDemoResult(
                instruction=normalized_instruction,
                success=True,
                content=prediction.reasoning,
                steps=steps,
                observations=observations,
                final_robot_state=self._snapshot_robot_state(),
            )

        last_observation = vision_step.observation

        for action in prediction.actions:

            action_step = self._run_robot_action_step(
                action.name,
                action.parameters,
            )
            steps.append(action_step)

            if not action_step.success or action_step.observation is None:

                return EmbodiedDemoResult(
                    instruction=normalized_instruction,
                    success=False,
                    content=f"机器人动作 {action.name} 执行失败。",
                    steps=steps,
                    observations=observations,
                    final_robot_state=self._snapshot_robot_state(),
                )

            observations.append(action_step.observation)
            last_observation = action_step.observation

            follow_up = self._policy.predict(
                last_observation,
                normalized_instruction,
            )

            if follow_up.completed:

                steps.append(
                    EmbodiedDemoStep(
                        phase="complete",
                        description="Policy 判定任务完成",
                        policy_prediction=follow_up,
                        success=True,
                        detail=follow_up.reasoning,
                    )
                )

                return EmbodiedDemoResult(
                    instruction=normalized_instruction,
                    success=True,
                    content=follow_up.reasoning,
                    steps=steps,
                    observations=observations,
                    final_robot_state=self._snapshot_robot_state(),
                )

        return EmbodiedDemoResult(
            instruction=normalized_instruction,
            success=False,
            content="动作已执行，但 Policy 未判定任务完成。",
            steps=steps,
            observations=observations,
            final_robot_state=self._snapshot_robot_state(),
        )

    def _snapshot_robot_state(self) -> dict:

        robot_state = self._robot.get_state()

        return {
            "provider": robot_state.provider,
            "position": robot_state.position,
            "holding": robot_state.holding,
            "status": robot_state.status,
            "metadata": robot_state.metadata,
        }

    def _run_vision_step(
        self,
        instruction: str,
    ) -> EmbodiedDemoStep:

        tool_result = self._tool_manager.execute(
            ToolContext(
                tool_name="analyze_image",
                arguments={
                    "image": self.DEFAULT_IMAGE,
                    "prompt": (
                        f"{self.DEFAULT_VISION_PROMPT}。"
                        f"任务指令：{instruction}"
                    ),
                },
            )
        )

        observation = ObservationFactory.from_tool_result(
            tool_result,
            tool_name="analyze_image",
        )

        return EmbodiedDemoStep(
            phase="vision",
            description="调用 VisionTool 观察环境",
            tool_name="analyze_image",
            tool_arguments={
                "image": self.DEFAULT_IMAGE,
                "prompt": instruction,
            },
            observation=observation,
            success=tool_result.success,
            detail=observation.content,
        )

    def _run_robot_action_step(
        self,
        tool_name: str,
        arguments: dict,
    ) -> EmbodiedDemoStep:

        tool_result = self._tool_manager.execute(
            ToolContext(
                tool_name=tool_name,
                arguments=arguments,
            )
        )

        observation = ObservationFactory.from_tool_result(
            tool_result,
            tool_name=tool_name,
        )

        return EmbodiedDemoStep(
            phase="robot",
            description=f"调用 RobotTool 执行 {tool_name}",
            tool_name=tool_name,
            tool_arguments=arguments,
            observation=observation,
            success=tool_result.success,
            detail=observation.content,
        )
