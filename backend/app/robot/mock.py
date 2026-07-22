from typing import Any

from app.robot.base import BaseRobot
from app.robot.exceptions import RobotActionError
from app.robot.types import RobotActionResult
from app.robot.types import RobotProviderType
from app.robot.types import RobotState


class MockRobot(BaseRobot):
    """
    模拟机器人实现。

    不连接真实硬件，在内存中维护位置与抓取状态，
    便于本地开发、单元测试及具身智能 Demo（Task13.8）。
    """

    _LOCATION_PRESETS: dict[str, dict[str, float]] = {
        "home": {"x": 0.0, "y": 0.0, "z": 0.0},
        "origin": {"x": 0.0, "y": 0.0, "z": 0.0},
        "table": {"x": 0.8, "y": 0.2, "z": 0.75},
        "desk": {"x": 0.8, "y": 0.2, "z": 0.75},
        "shelf": {"x": 1.2, "y": -0.3, "z": 1.0},
    }

    def __init__(self) -> None:

        self._position = dict(self._LOCATION_PRESETS["home"])
        self._holding: str | None = None
        self._status = "idle"

    @property
    def name(self) -> str:

        return RobotProviderType.MOCK.value

    def move(
        self,
        target: str | dict[str, Any],
    ) -> RobotActionResult:

        self._status = "moving"

        try:

            destination = self._resolve_target(target)

        except RobotActionError as error:

            self._status = "idle"

            return self._build_result(
                success=False,
                action="move",
                message=str(error),
            )

        self._position = destination
        self._status = "idle"

        return self._build_result(
            success=True,
            action="move",
            message=(
                f"机器人已移动到 "
                f"({destination['x']}, {destination['y']}, {destination['z']})"
            ),
            metadata={
                "target": target,
                "destination": destination,
            },
        )

    def grasp(
        self,
        target: str,
    ) -> RobotActionResult:

        object_name = (target or "").strip()

        if not object_name:

            return self._build_result(
                success=False,
                action="grasp",
                message="grasp 目标不能为空",
            )

        if self._holding is not None:

            return self._build_result(
                success=False,
                action="grasp",
                message=(
                    f"机器人已抓取 {self._holding}，"
                    "请先 release 后再抓取新物体"
                ),
            )

        self._status = "grasping"
        self._holding = object_name
        self._status = "idle"

        return self._build_result(
            success=True,
            action="grasp",
            message=f"grasp success: {object_name}",
            metadata={
                "target": object_name,
            },
        )

    def release(self) -> RobotActionResult:

        if self._holding is None:

            return self._build_result(
                success=False,
                action="release",
                message="当前没有抓取物体，无需 release",
            )

        released_object = self._holding
        self._holding = None
        self._status = "idle"

        return self._build_result(
            success=True,
            action="release",
            message=f"release success: {released_object}",
            metadata={
                "released_object": released_object,
            },
        )

    def get_state(self) -> RobotState:

        return RobotState(
            provider=self.name,
            position=dict(self._position),
            holding=self._holding,
            status=self._status,
            metadata={
                "mode": "mock",
            },
        )

    def _resolve_target(
        self,
        target: str | dict[str, Any],
    ) -> dict[str, float]:

        if isinstance(target, dict):

            return self._normalize_coordinates(target)

        target_name = str(target).strip().lower()

        if not target_name:

            raise RobotActionError("move 目标不能为空")

        if target_name in self._LOCATION_PRESETS:

            return dict(self._LOCATION_PRESETS[target_name])

        if self._looks_like_coordinates(target_name):

            parts = [
                float(item.strip())
                for item in target_name.split(",")
            ]

            if len(parts) != 3:

                raise RobotActionError(
                    "坐标格式应为 x,y,z",
                )

            return {
                "x": parts[0],
                "y": parts[1],
                "z": parts[2],
            }

        raise RobotActionError(
            f"未知目标位置: {target}",
        )

    def _normalize_coordinates(
        self,
        coordinates: dict[str, Any],
    ) -> dict[str, float]:

        required_keys = ("x", "y", "z")

        for key in required_keys:

            if key not in coordinates:

                raise RobotActionError(
                    f"坐标缺少字段: {key}",
                )

        return {
            "x": float(coordinates["x"]),
            "y": float(coordinates["y"]),
            "z": float(coordinates["z"]),
        }

    def _looks_like_coordinates(
        self,
        value: str,
    ) -> bool:

        return "," in value

    def _build_result(
        self,
        *,
        success: bool,
        action: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> RobotActionResult:

        return RobotActionResult(
            success=success,
            action=action,
            message=message,
            provider=self.name,
            state=self.get_state(),
            metadata=metadata or {},
        )
