from abc import ABC
from abc import abstractmethod
from typing import Any

from app.embodied.types import Observation
from app.policy.types import PolicyPrediction


class BasePolicy(ABC):
    """
    策略模型抽象接口。

    单一职责：根据环境 Observation 与任务指令预测下一步动作。
    后续可替换为 OpenVLA、RT-2、π0 等真实 VLA / 机器人策略模型。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Policy Provider 名称。"""

    @abstractmethod
    def predict(
        self,
        observation: Observation | dict[str, Any] | str,
        instruction: str,
    ) -> PolicyPrediction:
        """
        根据 Observation 与指令预测下一步动作。

        参数:
            observation: Observation 对象、字典或 JSON 字符串
            instruction: 用户任务指令，例如「帮我拿桌上的红色杯子」

        返回:
            PolicyPrediction，包含建议动作列表与推理说明
        """

        pass
