from __future__ import annotations

from pathlib import Path

from applications.software_team.config.defaults import DEFAULT_ENCODING
from applications.software_team.config.defaults import MAX_ARTIFACT_FILE_CHARS
from applications.software_team.project.artifacts.artifact_manager import (
    ArtifactManager,
)
from applications.software_team.project.models.artifact import Artifact


class ArtifactDependencyError(Exception):
    """
    产物依赖未满足时抛出。
    """


class ArtifactReader:
    """
    从 ArtifactManager 读取产物内容。

    所有 Agent 通过本类共享产物，不直接互相引用。
    """

    def resolve_dependencies(
        self,
        dependency_keys: tuple[str, ...],
        artifact_manager: ArtifactManager,
        workspace_path: str,
    ) -> dict[str, str]:
        """
        解析依赖并返回 {key: content} 供 PromptBuilder 注入 shared_context。
        """

        if not dependency_keys:

            return {}

        if dependency_keys == ("*",):

            return self._load_all_artifacts(
                artifact_manager,
                workspace_path,
            )

        resolved: dict[str, str] = {}

        for key in dependency_keys:

            if key.endswith(".md") or "." in key:

                resolved[key] = self._load_file_artifact(
                    key,
                    artifact_manager,
                )

            else:

                resolved[key] = self._load_directory_artifact(
                    key,
                    artifact_manager,
                    workspace_path,
                )

        return resolved

    def verify_dependencies(
        self,
        dependency_keys: tuple[str, ...],
        artifact_manager: ArtifactManager,
        workspace_path: str,
    ) -> None:
        """
        验证依赖是否满足，不满足则抛出 ArtifactDependencyError。
        """

        if not dependency_keys or dependency_keys == ("*",):

            return

        for key in dependency_keys:

            if key.endswith(".md") or "." in key:

                if not self._find_by_name(key, artifact_manager):

                    raise ArtifactDependencyError(
                        f"缺少依赖产物: {key}"
                    )

            else:

                directory = Path(workspace_path) / key

                if not directory.exists():

                    artifact = self._find_directory_artifact(
                        key,
                        artifact_manager,
                    )

                    if artifact is None:

                        raise ArtifactDependencyError(
                            f"缺少依赖目录: {key}"
                        )

    @staticmethod
    def _find_by_name(
        name: str,
        artifact_manager: ArtifactManager,
    ) -> Artifact | None:

        for artifact in artifact_manager.list():

            if artifact.name == name:

                return artifact

        return None

    @staticmethod
    def _find_directory_artifact(
        directory_name: str,
        artifact_manager: ArtifactManager,
    ) -> Artifact | None:

        for artifact in artifact_manager.list():

            if (
                artifact.type == "directory"
                and artifact.name == directory_name
            ):

                return artifact

        return None

    def _load_file_artifact(
        self,
        name: str,
        artifact_manager: ArtifactManager,
    ) -> str:

        artifact = self._find_by_name(name, artifact_manager)

        if artifact is None:

            raise ArtifactDependencyError(
                f"无法读取产物: {name}"
            )

        path = Path(artifact.path)

        if not path.is_file():

            raise ArtifactDependencyError(
                f"产物文件不存在: {artifact.path}"
            )

        return self._truncate_text(
            path.read_text(
                encoding=DEFAULT_ENCODING,
                errors="replace",
            ),
            MAX_ARTIFACT_FILE_CHARS,
        )

    @staticmethod
    def _truncate_text(content: str, limit: int) -> str:

        if len(content) <= limit:

            return content

        return (
            f"{content[:limit]}\n\n"
            f"...[artifact truncated {len(content) - limit} chars]"
        )

    def _load_directory_artifact(
        self,
        directory_name: str,
        artifact_manager: ArtifactManager,
        workspace_path: str,
    ) -> str:

        directory = Path(workspace_path) / directory_name

        if not directory.exists():

            raise ArtifactDependencyError(
                f"依赖目录不存在: {directory}"
            )

        files = sorted(
            path
            for path in directory.rglob("*")
            if path.is_file()
        )

        if not files:

            return f"[{directory_name}] (empty directory)"

        sections: list[str] = []

        for file_path in files:

            if self._should_skip_artifact_file(file_path):

                continue

            relative = file_path.relative_to(directory)

            try:

                content = file_path.read_text(
                    encoding=DEFAULT_ENCODING,
                    errors="replace",
                )

            except (OSError, UnicodeDecodeError):

                content = "(binary or unreadable)"

            sections.append(
                f"--- {relative} ---\n{content[:2000]}"
            )

        if not sections:

            return f"[{directory_name}] (no readable text files)"

        return "\n\n".join(sections)

    def _load_all_artifacts(
        self,
        artifact_manager: ArtifactManager,
        workspace_path: str,
    ) -> dict[str, str]:

        resolved: dict[str, str] = {}

        for artifact in artifact_manager.list():

            key = f"artifact:{artifact.name}"

            if artifact.type == "directory":

                resolved[key] = self._load_directory_artifact(
                    artifact.name,
                    artifact_manager,
                    workspace_path,
                )

            else:

                path = Path(artifact.path)

                if path.is_file():

                    resolved[key] = path.read_text(
                        encoding=DEFAULT_ENCODING,
                        errors="replace",
                    )

                else:

                    resolved[key] = (
                        f"(missing file: {artifact.path})"
                    )

        return resolved

    @staticmethod
    def _should_skip_artifact_file(file_path: Path) -> bool:

        parts = {part.lower() for part in file_path.parts}

        if "__pycache__" in parts or ".git" in parts:

            return True

        suffix = file_path.suffix.lower()

        return suffix in {
            ".pyc",
            ".pyo",
            ".pyd",
            ".db",
            ".sqlite",
            ".sqlite3",
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".webp",
            ".ico",
            ".zip",
            ".tar",
            ".gz",
        }
