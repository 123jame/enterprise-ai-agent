from __future__ import annotations

from pathlib import Path

from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.execution.command_runner import CommandRunner
from applications.software_team.execution.execution_result import DetectedProject
from applications.software_team.execution.execution_result import ExecutionResult
from applications.software_team.execution.execution_result import ProjectType
from applications.software_team.execution.execution_strategy import (
    ExecutionStrategy,
)
from applications.software_team.execution.execution_strategy import (
    FastAPIExecutionStrategy,
)
from applications.software_team.execution.execution_strategy import (
    FrontendExecutionStrategy,
)
from applications.software_team.execution.execution_strategy import (
    StaticFrontendExecutionStrategy,
)
from applications.software_team.execution.execution_strategy import (
    PythonExecutionStrategy,
)
from applications.software_team.execution.project_detector import ProjectDetector


class ExecutionManager:
    """
    Software Team 统一代码执行入口。

    职责：
    - 扫描 Workspace 识别 Python / FastAPI / React / Vue 项目
    - 通过策略模式执行对应命令
    - 返回 ExecutionResult

    Agent / Coordinator 不得直接使用 subprocess，
    所有运行命令必须经过本类。
    """

    def __init__(
        self,
        settings: SoftwareTeamSettings | None = None,
        detector: ProjectDetector | None = None,
        command_runner: CommandRunner | None = None,
        strategies: list[ExecutionStrategy] | None = None,
    ):

        self._settings = settings or SoftwareTeamSettings()
        self._detector = detector or ProjectDetector()
        self._command_runner = command_runner or CommandRunner(
            timeout_seconds=self._settings.execution_timeout_seconds,
        )

        self._strategies = strategies or [
            FastAPIExecutionStrategy(),
            PythonExecutionStrategy(),
            FrontendExecutionStrategy(),
            StaticFrontendExecutionStrategy(),
        ]

    def execute(
        self,
        workspace: str | Path,
        *,
        install_dependencies: bool | None = None,
    ) -> ExecutionResult:
        """
        执行 Workspace 内所有可识别项目。

        参数:
            workspace: 项目根目录
            install_dependencies: 是否安装依赖；默认读取配置

        返回:
            ExecutionResult（含 sub_results 聚合）
        """

        workspace_path = Path(workspace).resolve()

        if not workspace_path.exists():

            return ExecutionResult(
                success=False,
                workspace_path=str(workspace_path),
                error_message=f"Workspace not found: {workspace_path}",
            )

        detected = self._detector.detect_all(workspace_path)

        if not detected:

            return ExecutionResult(
                success=True,
                workspace_path=str(workspace_path),
                metadata={
                    "message": "No executable project detected.",
                },
            )

        install = (
            install_dependencies
            if install_dependencies is not None
            else self._settings.execution_install_dependencies
        )

        results = [
            self._execute_project(project, install)
            for project in detected
        ]

        return ExecutionResult.aggregate(
            workspace_path=str(workspace_path),
            results=results,
        )

    def execute_target(
        self,
        workspace: str | Path,
        target: str,
        *,
        install_dependencies: bool | None = None,
    ) -> ExecutionResult:
        """
        仅执行指定子目录（如 backend / frontend）。
        """

        workspace_path = Path(workspace).resolve()
        detected = self._detector.detect_all(workspace_path)

        matched = [
            project
            for project in detected
            if project.name == target
        ]

        if not matched:

            return ExecutionResult(
                success=False,
                workspace_path=str(workspace_path),
                target=target,
                error_message=f"Target not found or not runnable: {target}",
            )

        install = (
            install_dependencies
            if install_dependencies is not None
            else self._settings.execution_install_dependencies
        )

        results = [
            self._execute_project(project, install)
            for project in matched
        ]

        return ExecutionResult.aggregate(
            workspace_path=str(workspace_path),
            results=results,
        )

    def detect(
        self,
        workspace: str | Path,
    ) -> list[DetectedProject]:
        """
        仅检测，不执行。
        """

        return self._detector.detect_all(
            Path(workspace).resolve(),
        )

    def _execute_project(
        self,
        project: DetectedProject,
        install_dependencies: bool,
    ) -> ExecutionResult:

        strategy = self._resolve_strategy(project.project_type)

        if strategy is None:

            return ExecutionResult(
                success=False,
                workspace_path=project.root_path,
                project_type=project.project_type,
                target=project.name,
                error_message=(
                    f"No execution strategy for {project.project_type.value}"
                ),
            )

        return strategy.execute(
            project,
            self._command_runner,
            install_dependencies=install_dependencies,
        )

    def _resolve_strategy(
        self,
        project_type: ProjectType,
    ) -> ExecutionStrategy | None:

        for strategy in self._strategies:

            if strategy.supports(project_type):

                return strategy

        return None
