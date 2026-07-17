from __future__ import annotations

import sys
from pathlib import Path

from applications.software_team.config.settings import SoftwareTeamSettings
from applications.software_team.deployment.deployment_result import BuildResult
from applications.software_team.execution.command_runner import CommandRunner
from applications.software_team.execution.execution_result import ProjectType
from applications.software_team.execution.project_detector import ProjectDetector


class BuildManager:
    """
    统一项目构建入口。

    支持 Python / FastAPI / React / Vue，命令经 CommandRunner 执行。
    """

    def __init__(
        self,
        settings: SoftwareTeamSettings | None = None,
        command_runner: CommandRunner | None = None,
        detector: ProjectDetector | None = None,
    ):

        self._settings = settings or SoftwareTeamSettings()
        self._runner = command_runner or CommandRunner(
            timeout_seconds=self._settings.deployment_timeout_seconds,
        )
        self._detector = detector or ProjectDetector()

    def build(
        self,
        workspace: str | Path,
    ) -> BuildResult:

        workspace_path = Path(workspace).resolve()
        detected = self._detector.detect_all(workspace_path)

        if not detected:

            return BuildResult(
                success=True,
                workspace_path=str(workspace_path),
                metadata={"message": "No build targets detected"},
            )

        results = [
            self.build_target(
                workspace_path,
                project.name,
                project.project_type,
            )
            for project in detected
        ]

        return BuildResult.aggregate(
            workspace_path=str(workspace_path),
            results=results,
        )

    def build_target(
        self,
        workspace: Path,
        target: str,
        project_type: ProjectType | None = None,
    ) -> BuildResult:

        workspace = workspace.resolve()
        target_path = workspace / target

        if project_type is None:

            for project in self._detector.detect_all(workspace):

                if project.name == target:

                    project_type = project.project_type

                    break

        if project_type in (
            ProjectType.FASTAPI,
            ProjectType.PYTHON,
        ):

            return self._build_python(target_path, target, project_type)

        if project_type in (
            ProjectType.REACT,
            ProjectType.VUE,
        ):

            return self._build_frontend(
                target_path,
                target,
                project_type,
            )

        return BuildResult(
            success=True,
            workspace_path=str(workspace),
            target=target,
            project_type="static",
            metadata={"skipped": True},
        )

    def _build_python(
        self,
        target_path: Path,
        target: str,
        project_type: ProjectType,
    ) -> BuildResult:

        commands: list[str] = []

        requirements = target_path / "requirements.txt"

        if (
            requirements.is_file()
            and self._settings.deployment_install_dependencies
        ):

            pip = self._runner.run(
                command=[
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    "requirements.txt",
                ],
                cwd=target_path,
            )

            commands.append(pip.command)

            if not pip.success:

                return self._to_build_result(
                    target_path.parent,
                    target,
                    project_type.value,
                    pip,
                    commands,
                )

        compile_result = self._runner.run(
            command=[
                sys.executable,
                "-m",
                "compileall",
                "-q",
                ".",
            ],
            cwd=target_path,
        )

        commands.append(compile_result.command)

        if not compile_result.success:

            return self._to_build_result(
                target_path.parent,
                target,
                project_type.value,
                compile_result,
                commands,
            )

        if (target_path / "main.py").is_file():

            import_result = self._runner.run(
                command=[
                    sys.executable,
                    "-c",
                    "from main import app",
                ],
                cwd=target_path,
            )

            commands.append(import_result.command)

            return self._to_build_result(
                target_path.parent,
                target,
                project_type.value,
                import_result,
                commands,
            )

        return self._to_build_result(
            target_path.parent,
            target,
            project_type.value,
            compile_result,
            commands,
        )

    def _build_frontend(
        self,
        target_path: Path,
        target: str,
        project_type: ProjectType,
    ) -> BuildResult:

        package_json = target_path / "package.json"

        if not package_json.is_file():

            return BuildResult(
                success=True,
                workspace_path=str(target_path.parent),
                target=target,
                project_type=project_type.value,
                metadata={"skipped": "no package.json"},
            )

        if not self._settings.deployment_install_dependencies:

            return BuildResult(
                success=True,
                workspace_path=str(target_path.parent),
                target=target,
                project_type=project_type.value,
                metadata={"skipped": "npm install disabled"},
            )

        install = self._runner.run(
            command=["npm", "install"],
            cwd=target_path,
        )

        commands = [install.command]

        if not install.success:

            return self._to_build_result(
                target_path.parent,
                target,
                project_type.value,
                install,
                commands,
            )

        build = self._runner.run(
            command=["npm", "run", "build", "--if-present"],
            cwd=target_path,
        )

        commands.append(build.command)

        return self._to_build_result(
            target_path.parent,
            target,
            project_type.value,
            build,
            commands,
        )

    @staticmethod
    def _to_build_result(
        workspace: Path,
        target: str,
        project_type: str,
        command_result,
        commands: list[str],
    ) -> BuildResult:

        return BuildResult(
            success=command_result.success,
            workspace_path=str(workspace),
            target=target,
            project_type=project_type,
            command=" && ".join(commands),
            stdout=command_result.stdout,
            stderr=command_result.stderr,
            error_message=command_result.error_message,
            duration_ms=command_result.duration_ms,
        )
