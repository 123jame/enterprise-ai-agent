"""
Task13.2 Vision Tool 测试。

运行:
    cd backend
    python -m app.vision.tests.test_vision_tool
"""

from __future__ import annotations

import json

from app.tools.factory import ToolFactory
from app.tools.manager import ToolManager
from app.tools.registry import ToolRegistry
from app.tools.types import ToolContext
from app.vision.tool_registrar import register_vision_tools
from app.vision.tool_registrar import reset_vision_tool_registration
from app.vision.vision_tool import AnalyzeImageTool


def test_analyze_image_tool_schema() -> None:

    tool = AnalyzeImageTool()

    assert tool.name == "analyze_image"
    assert tool.schema["function"]["name"] == "analyze_image"
    assert "image" in tool.schema["function"]["parameters"]["properties"]
    assert "prompt" in tool.schema["function"]["parameters"]["properties"]


def test_analyze_image_tool_execute_success() -> None:

    tool = AnalyzeImageTool()
    context = ToolContext(
        tool_name="analyze_image",
        arguments={
            "image": "mock-image-base64",
            "prompt": "帮我找桌上的红色杯子",
        },
    )

    result = tool.execute(context)

    assert result.success is True

    payload = json.loads(result.content)

    assert payload["type"] == "vision"
    assert "red cup" in payload["content"]
    assert "red cup" in payload["detected_objects"]


def test_analyze_image_tool_missing_arguments() -> None:

    tool = AnalyzeImageTool()

    missing_image = tool.execute(
        ToolContext(
            tool_name="analyze_image",
            arguments={"prompt": "test"},
        )
    )

    assert missing_image.success is False

    missing_prompt = tool.execute(
        ToolContext(
            tool_name="analyze_image",
            arguments={"image": "mock-image"},
        )
    )

    assert missing_prompt.success is False


def test_tool_registry_and_manager_integration() -> None:

    reset_vision_tool_registration()
    ToolFactory._initialized = False

    ToolFactory.initialize()

    registered = ToolRegistry.get("analyze_image")

    assert isinstance(registered, AnalyzeImageTool)

    schemas = ToolManager().get_schemas()
    schema_names = [
        item["function"]["name"]
        for item in schemas
    ]

    assert "analyze_image" in schema_names

    manager_result = ToolManager().execute(
        ToolContext(
            tool_name="analyze_image",
            arguments={
                "image": "mock-image-base64",
                "prompt": "查看红色杯子",
            },
        )
    )

    assert manager_result.success is True

    payload = json.loads(manager_result.content)

    assert payload["type"] == "vision"


def run_all_tests() -> None:

    test_analyze_image_tool_schema()
    test_analyze_image_tool_execute_success()
    test_analyze_image_tool_missing_arguments()
    test_tool_registry_and_manager_integration()

    print("Task13.2 Vision Tool tests passed.")


if __name__ == "__main__":

    run_all_tests()
