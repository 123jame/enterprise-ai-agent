from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any


class VisionProviderType(str, Enum):
    """
    视觉模型提供方类型。

    当前仅实现 MOCK；其余类型预留，便于后续替换为真实模型。
    """

    MOCK = "mock"

    # 预留扩展：OpenAI Vision / Qwen-VL / LLaVA / CLIP
    OPENAI = "openai"
    QWEN_VL = "qwen_vl"
    LLAVA = "llava"
    CLIP = "clip"


@dataclass
class VisionImage:
    """
    视觉模块统一图像输入。

    支持文件路径、Base64 字符串或原始字节，便于 Tool 与 Agent 传递。
    """

    data: str | bytes

    media_type: str = "image/jpeg"

    source_path: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )


@dataclass
class VisionAnalysisResult:
    """
    视觉分析结果。

    content 为自然语言描述，后续 Observation 模块可直接消费。
    """

    content: str

    provider: str

    prompt: str

    detected_objects: list[str] = field(
        default_factory=list,
    )

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )
