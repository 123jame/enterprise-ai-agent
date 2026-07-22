from pathlib import Path

from app.vision.base import BaseVisionProvider
from app.vision.exceptions import VisionProviderError
from app.vision.types import VisionAnalysisResult
from app.vision.types import VisionImage
from app.vision.types import VisionProviderType


class MockVisionProvider(BaseVisionProvider):
    """
    模拟视觉 Provider。

    不调用真实 Vision API，基于 prompt 关键词返回确定性模拟结果，
    便于本地开发、单元测试及具身智能 Demo（Task13.8）。
    """

    _KEYWORD_OBJECTS: dict[str, list[str]] = {
        "红": ["red cup", "红色杯子"],
        "红色": ["red cup", "红色杯子"],
        "cup": ["red cup", "杯子"],
        "杯子": ["red cup", "红色杯子"],
        "桌": ["table", "桌子"],
        "桌上": ["table", "桌子", "red cup", "红色杯子"],
        "蓝色": ["blue bottle", "蓝色瓶子"],
        "手机": ["phone", "手机"],
        "书": ["book", "书本"],
    }

    @property
    def name(self) -> str:

        return VisionProviderType.MOCK.value

    def analyze(
        self,
        image: VisionImage | str | bytes,
        prompt: str,
    ) -> VisionAnalysisResult:

        normalized_image = self._normalize_image(image)
        normalized_prompt = (prompt or "").strip()

        if not normalized_prompt:

            raise VisionProviderError(
                "视觉分析 prompt 不能为空",
            )

        detected_objects = self._detect_objects(normalized_prompt)
        content = self._build_content(
            normalized_prompt,
            detected_objects,
            normalized_image,
        )

        return VisionAnalysisResult(
            content=content,
            provider=self.name,
            prompt=normalized_prompt,
            detected_objects=detected_objects,
            metadata={
                "mode": "mock",
                "image_source": normalized_image.source_path or "inline",
                "media_type": normalized_image.media_type,
                "image_size": self._estimate_image_size(
                    normalized_image.data,
                ),
            },
        )

    def _normalize_image(
        self,
        image: VisionImage | str | bytes,
    ) -> VisionImage:

        if isinstance(image, VisionImage):

            return image

        if isinstance(image, bytes):

            return VisionImage(
                data=image,
                media_type="image/jpeg",
            )

        image_text = str(image).strip()

        if not image_text:

            raise VisionProviderError(
                "视觉分析 image 不能为空",
            )

        path = Path(image_text)

        if path.exists() and path.is_file():

            return VisionImage(
                data=path.read_bytes(),
                media_type=self._guess_media_type(path.suffix),
                source_path=str(path),
            )

        return VisionImage(
            data=image_text,
            media_type="image/jpeg",
            metadata={
                "encoding": "base64_or_path_reference",
            },
        )

    def _detect_objects(
        self,
        prompt: str,
    ) -> list[str]:

        prompt_lower = prompt.lower()
        detected: list[str] = []

        for keyword, objects in self._KEYWORD_OBJECTS.items():

            if keyword.lower() in prompt_lower:

                for item in objects:

                    if item not in detected:

                        detected.append(item)

        if not detected:

            detected = ["unknown object", "未识别物体"]

        return detected

    def _build_content(
        self,
        prompt: str,
        detected_objects: list[str],
        image: VisionImage,
    ) -> str:

        object_text = "、".join(detected_objects)
        source = image.source_path or "当前图像"

        return (
            f"[Mock Vision] 已分析 {source}。"
            f"根据指令「{prompt}」，检测到：{object_text}。"
            f"场景理解：目标物体位于桌面可见区域，可进行后续抓取规划。"
        )

    def _estimate_image_size(
        self,
        data: str | bytes,
    ) -> int:

        if isinstance(data, bytes):

            return len(data)

        return len(data.encode("utf-8"))

    def _guess_media_type(
        self,
        suffix: str,
    ) -> str:

        mapping = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".gif": "image/gif",
        }

        return mapping.get(
            suffix.lower(),
            "application/octet-stream",
        )
