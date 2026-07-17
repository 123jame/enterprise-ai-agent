from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any


class DeployMode(str, Enum):
    """
    部署模式。
    """

    LOCAL = "local"
    DOCKER = "docker"
    REMOTE = "remote"


class DeploymentEventType(str, Enum):
    """
    Memory 事件类型。
    """

    BUILD = "build_history"
    PACKAGE = "package_history"
    DEPLOY = "deployment_history"
    HEALTH = "health_check"
    RELEASE = "release_history"


@dataclass
class BuildResult:
    """
    构建结果。
    """

    success: bool

    workspace_path: str

    target: str = ""

    project_type: str = ""

    command: str = ""

    stdout: str = ""

    stderr: str = ""

    error_message: str = ""

    duration_ms: float = 0.0

    sub_results: list[BuildResult] = field(
        default_factory=list,
    )

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )

    @classmethod
    def aggregate(
        cls,
        *,
        workspace_path: str,
        results: list[BuildResult],
    ) -> BuildResult:

        if not results:

            return cls(
                success=True,
                workspace_path=workspace_path,
                metadata={"message": "No build targets"},
            )

        failed = [r for r in results if not r.success]

        return cls(
            success=len(failed) == 0,
            workspace_path=workspace_path,
            target="aggregate",
            stdout="\n".join(r.stdout for r in results if r.stdout),
            stderr="\n".join(r.stderr for r in results if r.stderr),
            error_message="; ".join(
                r.error_message for r in failed if r.error_message
            ),
            duration_ms=sum(r.duration_ms for r in results),
            sub_results=results,
            metadata={"built_count": len(results), "failed": len(failed)},
        )


@dataclass
class PackageResult:
    """
    打包结果。
    """

    success: bool

    workspace_path: str

    package_path: str = ""

    package_type: str = ""

    artifacts: list[str] = field(
        default_factory=list,
    )

    error_message: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )


@dataclass
class DeployResult:
    """
    部署结果。
    """

    success: bool

    workspace_path: str

    mode: DeployMode = DeployMode.LOCAL

    message: str = ""

    deploy_url: str = ""

    stdout: str = ""

    stderr: str = ""

    error_message: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )


@dataclass
class HealthResult:
    """
    健康检查结果。
    """

    success: bool

    workspace_path: str

    checks: list[dict[str, Any]] = field(
        default_factory=list,
    )

    error_message: str = ""

    deploy_url: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )

    @property
    def summary(self) -> str:

        lines = [f"Health: {'PASS' if self.success else 'FAIL'}"]

        for check in self.checks:

            status = "PASS" if check.get("success") else "FAIL"

            lines.append(
                f"- [{status}] {check.get('name')}: "
                f"{check.get('message', '')}"
            )

        return "\n".join(lines)


@dataclass
class ReleaseResult:
    """
    发布结果。
    """

    success: bool

    workspace_path: str

    version: str = ""

    tag: str = ""

    release_notes_path: str = ""

    archive_path: str = ""

    error_message: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )


@dataclass
class DeploymentContext:
    """
    部署上下文，供 PromptBuilder 注入。
    """

    build_summary: str = ""

    package_summary: str = ""

    deploy_summary: str = ""

    health_summary: str = ""

    release_summary: str = ""

    deploy_url: str = ""

    version: str = ""

    def to_shared_context(self) -> dict[str, str]:

        return {
            "deployment_build_result": self.build_summary,
            "deployment_package_result": self.package_summary,
            "deployment_deploy_result": self.deploy_summary,
            "deployment_health_result": self.health_summary,
            "deployment_release_result": self.release_summary,
            "deployment_url": self.deploy_url,
            "deployment_version": self.version,
        }

    def to_prompt_block(self) -> str:

        return (
            f"Version: {self.version or 'n/a'}\n"
            f"Deploy URL: {self.deploy_url or 'n/a'}\n\n"
            f"Build:\n{self.build_summary or 'n/a'}\n\n"
            f"Package:\n{self.package_summary or 'n/a'}\n\n"
            f"Deploy:\n{self.deploy_summary or 'n/a'}\n\n"
            f"Health:\n{self.health_summary or 'n/a'}\n\n"
            f"Release:\n{self.release_summary or 'n/a'}"
        )


@dataclass
class DeploymentPipelineResult:
    """
    完整部署流水线结果。
    """

    success: bool

    build: BuildResult | None = None

    package: PackageResult | None = None

    deploy: DeployResult | None = None

    health: HealthResult | None = None

    release: ReleaseResult | None = None

    context: DeploymentContext = field(
        default_factory=DeploymentContext,
    )

    error_message: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )
