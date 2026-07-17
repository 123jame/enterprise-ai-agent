from __future__ import annotations

import json
import shutil
from pathlib import Path

from applications.software_team.execution.execution_result import DetectedProject
from applications.software_team.execution.execution_result import ProjectType


class ProjectDetector:
    """
    扫描 Workspace，识别可执行的子项目。

    单一职责：结构检测，不执行命令。
    """

    BACKEND_DIR = "backend"
    FRONTEND_DIR = "frontend"

    def detect_all(
        self,
        workspace: Path,
    ) -> list[DetectedProject]:
        """
        检测 Workspace 内所有可执行子项目。
        """

        workspace = workspace.resolve()
        detected: list[DetectedProject] = []

        backend = workspace / self.BACKEND_DIR

        if backend.is_dir():

            backend_type = self._detect_python_project(backend)

            detected.append(
                DetectedProject(
                    project_type=backend_type,
                    root_path=str(backend),
                    name=self.BACKEND_DIR,
                    metadata=self._collect_python_metadata(backend),
                )
            )

        frontend = workspace / self.FRONTEND_DIR

        if frontend.is_dir():

            frontend_type = self._detect_frontend_project(frontend)

            if frontend_type != ProjectType.UNKNOWN:

                detected.append(
                    DetectedProject(
                        project_type=frontend_type,
                        root_path=str(frontend),
                        name=self.FRONTEND_DIR,
                        metadata=self._collect_frontend_metadata(frontend),
                    )
                )

            elif (frontend / "index.html").is_file():

                detected.append(
                    DetectedProject(
                        project_type=ProjectType.STATIC,
                        root_path=str(frontend),
                        name=self.FRONTEND_DIR,
                        metadata=self._collect_frontend_metadata(frontend),
                    )
                )

        if not detected and self._looks_like_python_project(workspace):

            detected.append(
                DetectedProject(
                    project_type=self._detect_python_project(workspace),
                    root_path=str(workspace),
                    name=workspace.name,
                    metadata=self._collect_python_metadata(workspace),
                )
            )

        return detected

    def _detect_python_project(
        self,
        root: Path,
    ) -> ProjectType:

        requirements = root / "requirements.txt"
        main_py = root / "main.py"

        if main_py.is_file() and requirements.is_file():

            text = requirements.read_text(
                encoding="utf-8",
            ).lower()

            if "fastapi" in text:

                return ProjectType.FASTAPI

        if any(root.glob("*.py")):

            return ProjectType.PYTHON

        return ProjectType.UNKNOWN

    def _detect_frontend_project(
        self,
        root: Path,
    ) -> ProjectType:

        package_json = root / "package.json"

        if not package_json.is_file():

            if (root / "index.html").is_file():

                return ProjectType.UNKNOWN

            return ProjectType.UNKNOWN

        try:

            payload = json.loads(
                package_json.read_text(encoding="utf-8")
            )

        except json.JSONDecodeError:

            return ProjectType.UNKNOWN

        deps = {
            **payload.get("dependencies", {}),
            **payload.get("devDependencies", {}),
        }

        if "react" in deps:

            return ProjectType.REACT

        if "vue" in deps:

            return ProjectType.VUE

        if (root / "index.html").is_file():

            return ProjectType.UNKNOWN

        return ProjectType.UNKNOWN

    @staticmethod
    def _looks_like_python_project(
        root: Path,
    ) -> bool:

        return (
            (root / "requirements.txt").is_file()
            or any(root.glob("*.py"))
        )

    @staticmethod
    def _collect_python_metadata(
        root: Path,
    ) -> dict[str, str]:

        metadata: dict[str, str] = {}

        requirements = root / "requirements.txt"

        if requirements.is_file():

            metadata["requirements"] = requirements.name

        main_py = root / "main.py"

        if main_py.is_file():

            metadata["entrypoint"] = main_py.name

        return metadata

    @staticmethod
    def _collect_frontend_metadata(
        root: Path,
    ) -> dict[str, str]:

        metadata: dict[str, str] = {}
        package_json = root / "package.json"

        if package_json.is_file():

            metadata["package_json"] = package_json.name

        if shutil.which("npm"):

            metadata["npm_available"] = "true"

        else:

            metadata["npm_available"] = "false"

        return metadata
