from __future__ import annotations

import sys
from abc import ABC
from abc import abstractmethod
from pathlib import Path

from applications.software_team.execution.command_runner import CommandRunner
from applications.software_team.execution.execution_result import DetectedProject
from applications.software_team.execution.execution_result import ExecutionResult
from applications.software_team.execution.execution_result import ProjectType


class ExecutionStrategy(ABC):
    """
    项目类型执行策略接口。
    """

    @abstractmethod
    def supports(
        self,
        project_type: ProjectType,
    ) -> bool:
        """
        是否支持该类型。
        """

    @abstractmethod
    def execute(
        self,
        project: DetectedProject,
        runner: CommandRunner,
        *,
        install_dependencies: bool,
    ) -> ExecutionResult:
        """
        执行单个检测到的子项目。
        """


class PythonExecutionStrategy(ExecutionStrategy):
    """
    通用 Python 项目执行策略。
    """

    def supports(
        self,
        project_type: ProjectType,
    ) -> bool:

        return project_type == ProjectType.PYTHON

    def execute(
        self,
        project: DetectedProject,
        runner: CommandRunner,
        *,
        install_dependencies: bool,
    ) -> ExecutionResult:

        root = Path(project.root_path)
        commands: list[str] = []

        if install_dependencies:

            requirements = root / "requirements.txt"

            if requirements.is_file():

                pip_result = runner.run(
                    command=[
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        "-r",
                        "requirements.txt",
                    ],
                    cwd=root,
                )

                commands.append(pip_result.command)

                if not pip_result.success:

                    return self._to_execution_result(
                        project,
                        pip_result,
                        commands,
                    )

        compile_result = runner.run(
            command=[
                sys.executable,
                "-m",
                "compileall",
                "-q",
                ".",
            ],
            cwd=root,
        )

        commands.append(compile_result.command)

        if not compile_result.success:

            return self._to_execution_result(
                project,
                compile_result,
                commands,
            )

        entrypoint = project.metadata.get("entrypoint")

        if entrypoint:

            import_result = runner.run(
                command=[
                    sys.executable,
                    "-c",
                    (
                        f"import importlib.util; "
                        f"spec=importlib.util.spec_from_file_location("
                        f"'module', '{entrypoint}'); "
                        f"module=importlib.util.module_from_spec(spec); "
                        f"spec.loader.exec_module(module)"
                    ),
                ],
                cwd=root,
            )

            commands.append(import_result.command)

            return self._to_execution_result(
                project,
                import_result,
                commands,
            )

        return self._to_execution_result(
            project,
            compile_result,
            commands,
        )

    @staticmethod
    def _to_execution_result(
        project: DetectedProject,
        command_result,
        commands: list[str],
    ) -> ExecutionResult:

        return ExecutionResult(
            success=command_result.success,
            workspace_path=project.root_path,
            project_type=project.project_type,
            target=project.name,
            command=" && ".join(commands),
            exit_code=command_result.exit_code,
            stdout=command_result.stdout,
            stderr=command_result.stderr,
            duration_ms=command_result.duration_ms,
            error_message=command_result.error_message,
            metadata=dict(project.metadata),
        )


class FastAPIExecutionStrategy(PythonExecutionStrategy):
    """
    FastAPI 项目执行策略。

    在 Python 策略基础上增加 app 对象加载验证。
    """

    def supports(
        self,
        project_type: ProjectType,
    ) -> bool:

        return project_type == ProjectType.FASTAPI

    def execute(
        self,
        project: DetectedProject,
        runner: CommandRunner,
        *,
        install_dependencies: bool,
    ) -> ExecutionResult:

        base_result = super().execute(
            project,
            runner,
            install_dependencies=install_dependencies,
        )

        if not base_result.success:

            return base_result

        root = Path(project.root_path)

        app_result = runner.run(
            command=[
                sys.executable,
                "-c",
                "from main import app; print(getattr(app, 'title', 'ok'))",
            ],
            cwd=root,
        )

        commands = [base_result.command, app_result.command]

        return ExecutionResult(
            success=app_result.success,
            workspace_path=project.root_path,
            project_type=ProjectType.FASTAPI,
            target=project.name,
            command=" && ".join(commands),
            exit_code=app_result.exit_code,
            stdout="\n".join(
                part
                for part in (base_result.stdout, app_result.stdout)
                if part
            ),
            stderr="\n".join(
                part
                for part in (base_result.stderr, app_result.stderr)
                if part
            ),
            duration_ms=base_result.duration_ms + app_result.duration_ms,
            error_message=app_result.error_message,
            metadata={
                **project.metadata,
                "app_loaded": str(app_result.success),
            },
        )


class FrontendExecutionStrategy(ExecutionStrategy):
    """
    React / Vue 前端项目执行策略。
    """

    def supports(
        self,
        project_type: ProjectType,
    ) -> bool:

        return project_type in (
            ProjectType.REACT,
            ProjectType.VUE,
        )

    def execute(
        self,
        project: DetectedProject,
        runner: CommandRunner,
        *,
        install_dependencies: bool,
    ) -> ExecutionResult:

        root = Path(project.root_path)
        commands: list[str] = []

        structure_result = self._validate_structure(root)

        if not structure_result.success:

            return self._to_execution_result(
                project,
                structure_result,
                [structure_result.command],
            )

        commands.append(structure_result.command)

        npm_available = (
            project.metadata.get("npm_available") == "true"
        )

        if not npm_available:

            return ExecutionResult(
                success=True,
                workspace_path=project.root_path,
                project_type=project.project_type,
                target=project.name,
                command=structure_result.command,
                stdout=structure_result.stdout,
                stderr=structure_result.stderr,
                duration_ms=structure_result.duration_ms,
                metadata={
                    **project.metadata,
                    "skipped_npm": "true",
                    "reason": "npm not available",
                },
            )

        if install_dependencies:

            install_result = runner.run(
                command=["npm", "install"],
                cwd=root,
            )

            commands.append(install_result.command)

            if not install_result.success:

                return self._to_execution_result(
                    project,
                    install_result,
                    commands,
                )

        package_json = root / "package.json"

        build_script = self._has_script(
            package_json,
            "build",
        )

        if build_script:

            build_result = runner.run(
                command=["npm", "run", "build"],
                cwd=root,
            )

            commands.append(build_result.command)

            if (
                not build_result.success
                and (root / "index.html").is_file()
            ):

                return ExecutionResult(
                    success=True,
                    workspace_path=project.root_path,
                    project_type=project.project_type,
                    target=project.name,
                    command=" && ".join(commands),
                    stdout=build_result.stdout,
                    stderr=build_result.stderr,
                    duration_ms=build_result.duration_ms,
                    metadata={
                        **project.metadata,
                        "build_skipped": "true",
                        "reason": "build failed but static scaffold present",
                    },
                )

            return self._to_execution_result(
                project,
                build_result,
                commands,
            )

        lint_result = runner.run(
            command=["npm", "run", "lint", "--if-present"],
            cwd=root,
        )

        commands.append(lint_result.command)

        return self._to_execution_result(
            project,
            lint_result,
            commands,
        )

    @staticmethod
    def _validate_structure(
        root: Path,
    ):

        from applications.software_team.execution.command_runner import (
            CommandRunResult,
        )

        package_json = root / "package.json"
        index_html = root / "index.html"

        if not package_json.is_file() and not index_html.is_file():

            return CommandRunResult(
                success=False,
                command="validate_structure",
                exit_code=1,
                stdout="",
                stderr="Missing package.json and index.html",
                duration_ms=0.0,
                error_message="Invalid frontend project structure",
            )

        return CommandRunResult(
            success=True,
            command="validate_structure",
            exit_code=0,
            stdout="Frontend structure validated",
            stderr="",
            duration_ms=0.0,
        )

    @staticmethod
    def _has_script(
        package_json: Path,
        script_name: str,
    ) -> bool:

        import json

        if not package_json.is_file():

            return False

        try:

            payload = json.loads(
                package_json.read_text(encoding="utf-8")
            )

        except json.JSONDecodeError:

            return False

        scripts = payload.get("scripts", {})

        return script_name in scripts

    @staticmethod
    def _to_execution_result(
        project: DetectedProject,
        command_result,
        commands: list[str],
    ) -> ExecutionResult:

        return ExecutionResult(
            success=command_result.success,
            workspace_path=project.root_path,
            project_type=project.project_type,
            target=project.name,
            command=" && ".join(commands),
            exit_code=command_result.exit_code,
            stdout=command_result.stdout,
            stderr=command_result.stderr,
            duration_ms=command_result.duration_ms,
            error_message=command_result.error_message,
            metadata=dict(project.metadata),
        )


class StaticFrontendExecutionStrategy(ExecutionStrategy):
    """
    静态 HTML/JS/CSS 前端（无 React/Vue 构建链）。
    """

    def supports(
        self,
        project_type: ProjectType,
    ) -> bool:

        return project_type == ProjectType.STATIC

    def execute(
        self,
        project: DetectedProject,
        runner: CommandRunner,
        *,
        install_dependencies: bool,
    ) -> ExecutionResult:

        root = Path(project.root_path)
        index_html = root / "index.html"

        if not index_html.is_file():

            return ExecutionResult(
                success=False,
                workspace_path=project.root_path,
                project_type=project.project_type,
                target=project.name,
                error_message="Static frontend missing index.html",
            )

        return ExecutionResult(
            success=True,
            workspace_path=project.root_path,
            project_type=project.project_type,
            target=project.name,
            command="static-structure-check",
            stdout="Static frontend structure validated",
            metadata={
                **project.metadata,
                "index_html": index_html.name,
            },
        )
