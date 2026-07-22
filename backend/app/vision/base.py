from abc import ABC
from abc import abstractmethod

from app.vision.types import VisionAnalysisResult
from app.vision.types import VisionImage


class BaseVisionProvider(ABC):
    """
    视觉能力抽象接口。

    单一职责：接收图像与分析指令，返回结构化视觉理解结果。
    后续可替换为 OpenAI Vision、Qwen-VL、LLaVA、CLIP 等实现。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider 名称，用于日志与 Observation 标记。"""

    @abstractmethod
    def analyze(
        self,
        image: VisionImage | str | bytes,
        prompt: str,
    ) -> VisionAnalysisResult:
        """
        分析图像内容。

        参数:
            image: VisionImage 对象、文件路径、Base64 字符串或原始字节
            prompt: 分析指令或提问，例如「描述桌上有什么物体」

        返回:
            VisionAnalysisResult，包含自然语言描述与检测到的物体列表
        """

        pass
