from typing import Any

from app.embodied.types import Observation
from app.policy.base import BasePolicy
from app.policy.exceptions import PolicyPredictionError
from app.policy.observation_adapter import normalize_observation_input
from app.policy.types import PolicyAction
from app.policy.types import PolicyPrediction
from app.policy.types import PolicyProviderType


class MockPolicy(BasePolicy):
    """
    模拟策略模型。

    基于规则将 Observation 映射为 Tool 动作建议，
    不调用真实 VLA 模型，便于本地开发与 Task13.8 Demo。
    """

    @property
    def name(self) -> str:

        return PolicyProviderType.MOCK.value

    def predict(
        self,
        observation: Observation | dict[str, Any] | str,
        instruction: str,
    ) -> PolicyPrediction:

        normalized_instruction = (instruction or "").strip()

        if not normalized_instruction:

            raise PolicyPredictionError(
                "Policy instruction 不能为空",
            )

        observation_payload = normalize_observation_input(
            observation,
        )

        observation_type = str(
            observation_payload.get("type", "generic")
        )
        observation_content = str(
            observation_payload.get("content", "")
        ).lower()

        if observation_type == "vision":

            return self._predict_from_vision(
                normalized_instruction,
                observation_content,
                observation_payload,
            )

        if observation_type == "robot":

            return self._predict_from_robot(
                normalized_instruction,
                observation_content,
                observation_payload,
            )

        return PolicyPrediction(
            provider=self.name,
            instruction=normalized_instruction,
            observation_type=observation_type,
            actions=[
                PolicyAction(
                    name="analyze_image",
                    parameters={
                        "image": "current_scene",
                        "prompt": normalized_instruction,
                    },
                    description="先观察环境以获取视觉信息",
                ),
            ],
            reasoning="当前缺少视觉 Observation，建议先调用 analyze_image。",
            confidence=0.55,
            metadata={
                "mode": "mock",
                "fallback": "request_vision",
            },
        )

    def _predict_from_vision(
        self,
        instruction: str,
        observation_content: str,
        observation_payload: dict[str, Any],
    ) -> PolicyPrediction:

        target_object = self._extract_target_object(
            instruction,
            observation_content,
            observation_payload,
        )

        actions = [
            PolicyAction(
                name="robot_move",
                parameters={"target": "table"},
                description="移动到桌子位置",
            ),
            PolicyAction(
                name="robot_grasp",
                parameters={"target": target_object},
                description=f"抓取目标物体 {target_object}",
            ),
        ]

        return PolicyPrediction(
            provider=self.name,
            instruction=instruction,
            observation_type="vision",
            actions=actions,
            reasoning=(
                f"视觉 Observation 已识别目标 {target_object}，"
                "建议先移动到 table，再执行 grasp。"
            ),
            confidence=0.82,
            metadata={
                "mode": "mock",
                "target_object": target_object,
            },
        )

    def _predict_from_robot(
        self,
        instruction: str,
        observation_content: str,
        observation_payload: dict[str, Any],
    ) -> PolicyPrediction:

        if "grasp success" in observation_content:

            return PolicyPrediction(
                provider=self.name,
                instruction=instruction,
                observation_type="robot",
                actions=[],
                reasoning="机器人已成功抓取目标物体，任务完成。",
                confidence=0.9,
                completed=True,
                metadata={
                    "mode": "mock",
                    "status": "grasp_success",
                },
            )

        if "release success" in observation_content:

            return PolicyPrediction(
                provider=self.name,
                instruction=instruction,
                observation_type="robot",
                actions=[],
                reasoning="机器人已成功释放物体，任务完成。",
                confidence=0.9,
                completed=True,
                metadata={
                    "mode": "mock",
                    "status": "release_success",
                },
            )

        return PolicyPrediction(
            provider=self.name,
            instruction=instruction,
            observation_type="robot",
            actions=[
                PolicyAction(
                    name="robot_release",
                    parameters={},
                    description="释放当前抓取物体",
                ),
            ],
            reasoning="检测到机器人动作反馈，建议根据当前状态执行 release。",
            confidence=0.6,
            metadata={
                "mode": "mock",
                "status": "robot_feedback",
            },
        )

    def _extract_target_object(
        self,
        instruction: str,
        observation_content: str,
        observation_payload: dict[str, Any],
    ) -> str:

        detected_objects = observation_payload.get(
            "detected_objects",
        )

        if isinstance(detected_objects, list) and detected_objects:

            for item in detected_objects:

                text = str(item).lower()

                if "cup" in text or "杯" in text:

                    return str(item)

            return str(detected_objects[0])

        instruction_lower = instruction.lower()

        if "红" in instruction or "red" in instruction_lower:

            return "red cup"

        if "杯" in instruction or "cup" in instruction_lower:

            return "cup"

        if observation_content:

            return observation_content.split("、")[0]

        return "target_object"
