"""
Task13.1 Vision Module 测试。

运行:
    cd backend
    python -m app.vision.tests.test_vision
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from app.vision.factory import get_vision_provider
from app.vision.factory import reset_vision_provider
from app.vision.mock import MockVisionProvider
from app.vision.registry import VisionProviderRegistry
from app.vision.types import VisionImage


def test_mock_provider_name() -> None:

    provider = MockVisionProvider()

    assert provider.name == "mock"


def test_analyze_with_prompt_keywords() -> None:

    provider = MockVisionProvider()

    result = provider.analyze(
        image="mock-image-base64",
        prompt="帮我找桌上的红色杯子",
    )

    assert "red cup" in result.detected_objects
    assert "红色杯子" in result.detected_objects
    assert result.provider == "mock"
    assert "Mock Vision" in result.content


def test_analyze_with_vision_image_object() -> None:

    provider = MockVisionProvider()

    result = provider.analyze(
        image=VisionImage(
            data=b"fake-image-bytes",
            media_type="image/png",
            source_path="/tmp/scene.png",
        ),
        prompt="描述图像中的物体",
    )

    assert result.metadata["mode"] == "mock"
    assert result.metadata["media_type"] == "image/png"
    assert result.metadata["image_size"] == len(b"fake-image-bytes")


def test_analyze_with_file_path() -> None:

    provider = MockVisionProvider()

    with tempfile.NamedTemporaryFile(
        suffix=".png",
        delete=False,
    ) as temp_file:

        temp_file.write(b"png-bytes")
        temp_path = temp_file.name

    try:

        result = provider.analyze(
            image=temp_path,
            prompt="查看红色杯子",
        )

        assert Path(temp_path).name in result.content
        assert "red cup" in result.detected_objects

    finally:

        Path(temp_path).unlink(missing_ok=True)


def test_registry_and_factory() -> None:

    reset_vision_provider()

    assert "mock" in VisionProviderRegistry.list_providers()

    provider = get_vision_provider("mock")

    assert isinstance(provider, MockVisionProvider)

    singleton = get_vision_provider()

    assert singleton is get_vision_provider()


def run_all_tests() -> None:

    test_mock_provider_name()
    test_analyze_with_prompt_keywords()
    test_analyze_with_vision_image_object()
    test_analyze_with_file_path()
    test_registry_and_factory()

    print("Task13.1 Vision Module tests passed.")


if __name__ == "__main__":

    run_all_tests()
