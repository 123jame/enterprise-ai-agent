from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class PlatformEventType(str, Enum):
    """
    Memory / Audit 平台事件类型。
    """

    ORGANIZATION = "platform_history"
    WORKSPACE = "platform_history"
    PROJECT = "platform_history"
    TEAM = "platform_history"
    MODEL = "platform_history"
    PERMISSION = "platform_history"
    AUDIT = "audit_history"
    CONFIG = "platform_history"
    GOVERNANCE = "platform_history"


class MemoryScope(str, Enum):
    """
    Memory 作用域。
    """

    ORGANIZATION = "organization"
    WORKSPACE = "workspace"
    PROJECT = "project"
    USER = "user"


class TeamType(str, Enum):
    """
    AI Team 类型。
    """

    SOFTWARE = "software_team"
    QA = "qa_team"
    RESEARCH = "research_team"
    SECURITY = "security_team"


class ModelProvider(str, Enum):
    """
    模型提供商。
    """

    OPENAI = "openai"
    CLAUDE = "claude"
    GEMINI = "gemini"
    LOCAL = "local"


class AuditCategory(str, Enum):
    """
    审计类别。
    """

    PROMPT = "prompt"
    TOOL_CALL = "tool_call"
    MEMORY = "memory"
    WORKFLOW = "workflow"
    DEPLOYMENT = "deployment"
    GIT = "git"
    PROJECT = "project"
    OPERATION = "operation"
    PLATFORM = "platform"


class PermissionAction(str, Enum):
    """
    权限动作。
    """

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


class PolicyType(str, Enum):
    """
    治理策略类型。
    """

    AGENT = "agent_policy"
    PROMPT = "prompt_policy"
    TOOL = "tool_policy"
    MODEL = "model_policy"


@dataclass
class Department:
    """
    组织部门。
    """

    id: str
    name: str
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, name: str, description: str = "") -> Department:

        return cls(
            id=f"dept_{uuid4().hex[:10]}",
            name=name,
            description=description,
        )


@dataclass
class Member:
    """
    组织成员。
    """

    id: str
    name: str
    email: str = ""
    role: str = "member"
    department_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        name: str,
        *,
        email: str = "",
        role: str = "member",
        department_id: str = "",
    ) -> Member:

        return cls(
            id=f"member_{uuid4().hex[:10]}",
            name=name,
            email=email,
            role=role,
            department_id=department_id,
        )


@dataclass
class Organization:
    """
    企业组织。
    """

    id: str
    name: str
    departments: list[Department] = field(default_factory=list)
    members: list[Member] = field(default_factory=list)
    teams: list[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, name: str) -> Organization:

        return cls(
            id=f"org_{uuid4().hex[:10]}",
            name=name,
        )


@dataclass
class EnterpriseWorkspace:
    """
    企业工作空间。
    """

    id: str
    name: str
    organization_id: str
    root_path: str
    project_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        name: str,
        organization_id: str,
        root_path: str,
    ) -> EnterpriseWorkspace:

        return cls(
            id=f"ws_{uuid4().hex[:10]}",
            name=name,
            organization_id=organization_id,
            root_path=root_path,
        )


@dataclass
class RegisteredProject:
    """
    平台注册项目。
    """

    id: str
    name: str
    organization_id: str
    workspace_id: str
    team_type: TeamType
    requirement: str = ""
    status: str = "created"
    owner_id: str = ""
    workspace_path: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        name: str,
        organization_id: str,
        workspace_id: str,
        team_type: TeamType = TeamType.SOFTWARE,
        requirement: str = "",
        owner_id: str = "",
        workspace_path: str = "",
    ) -> RegisteredProject:

        return cls(
            id=f"proj_{uuid4().hex[:12]}",
            name=name,
            organization_id=organization_id,
            workspace_id=workspace_id,
            team_type=team_type,
            requirement=requirement,
            owner_id=owner_id,
            workspace_path=workspace_path,
        )


@dataclass
class AITeam:
    """
    AI Team 定义。
    """

    id: str
    name: str
    team_type: TeamType
    organization_id: str
    agent_names: list[str] = field(default_factory=list)
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        name: str,
        team_type: TeamType,
        organization_id: str,
        agent_names: list[str] | None = None,
    ) -> AITeam:

        return cls(
            id=f"team_{uuid4().hex[:10]}",
            name=name,
            team_type=team_type,
            organization_id=organization_id,
            agent_names=agent_names or [],
        )


@dataclass
class ModelConfig:
    """
    模型配置。
    """

    id: str
    name: str
    provider: ModelProvider
    model_id: str
    enabled: bool = True
    priority: int = 100
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        name: str,
        provider: ModelProvider,
        model_id: str,
        priority: int = 100,
    ) -> ModelConfig:

        return cls(
            id=f"model_{uuid4().hex[:10]}",
            name=name,
            provider=provider,
            model_id=model_id,
            priority=priority,
        )


@dataclass
class Role:
    """
    权限角色。
    """

    id: str
    name: str
    permissions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, name: str, permissions: list[str] | None = None) -> Role:

        return cls(
            id=f"role_{uuid4().hex[:10]}",
            name=name,
            permissions=permissions or [],
        )


@dataclass
class PermissionGrant:
    """
    权限授予记录。
    """

    id: str
    subject_type: str
    subject_id: str
    resource_type: str
    resource_id: str
    action: PermissionAction
    granted: bool = True

    @classmethod
    def create(
        cls,
        *,
        subject_type: str,
        subject_id: str,
        resource_type: str,
        resource_id: str,
        action: PermissionAction,
    ) -> PermissionGrant:

        return cls(
            id=f"perm_{uuid4().hex[:10]}",
            subject_type=subject_type,
            subject_id=subject_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
        )


@dataclass
class AuditRecord:
    """
    审计记录。
    """

    id: str
    category: AuditCategory
    actor: str
    action: str
    resource: str
    detail: str
    timestamp: str = field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        category: AuditCategory,
        actor: str,
        action: str,
        resource: str,
        detail: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> AuditRecord:

        return cls(
            id=f"audit_{uuid4().hex[:12]}",
            category=category,
            actor=actor,
            action=action,
            resource=resource,
            detail=detail,
            metadata=metadata or {},
        )


@dataclass
class PlatformPolicy:
    """
    治理策略。
    """

    id: str
    policy_type: PolicyType
    name: str
    rules: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

    @classmethod
    def create(
        cls,
        *,
        policy_type: PolicyType,
        name: str,
        rules: dict[str, Any] | None = None,
    ) -> PlatformPolicy:

        return cls(
            id=f"policy_{uuid4().hex[:10]}",
            policy_type=policy_type,
            name=name,
            rules=rules or {},
        )


@dataclass
class MemoryScopeContext:
    """
    Memory 作用域上下文。
    """

    organization_id: str = ""
    workspace_id: str = ""
    project_id: str = ""
    user_id: str = ""

    def to_metadata(self) -> dict[str, str]:

        return {
            "memory_scope": MemoryScope.PROJECT.value,
            "organization_id": self.organization_id,
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "user_id": self.user_id,
        }


@dataclass
class PlatformContext:
    """
    平台上下文，供 PromptBuilder 注入。
    """

    organization_summary: str = ""
    workspace_summary: str = ""
    permission_summary: str = ""
    project_summary: str = ""
    team_summary: str = ""
    model_summary: str = ""
    governance_summary: str = ""

    def to_shared_context(self) -> dict[str, str]:

        return {
            "platform_organization": self.organization_summary,
            "platform_workspace": self.workspace_summary,
            "platform_permission": self.permission_summary,
            "platform_project": self.project_summary,
            "platform_team": self.team_summary,
            "platform_model": self.model_summary,
            "platform_governance": self.governance_summary,
        }

    def to_prompt_block(self) -> str:

        return (
            f"## Organization\n{self.organization_summary or 'n/a'}\n\n"
            f"## Workspace\n{self.workspace_summary or 'n/a'}\n\n"
            f"## Permission\n{self.permission_summary or 'n/a'}\n\n"
            f"## Project\n{self.project_summary or 'n/a'}\n\n"
            f"## Team\n{self.team_summary or 'n/a'}\n\n"
            f"## Model\n{self.model_summary or 'n/a'}\n\n"
            f"## Governance\n{self.governance_summary or 'n/a'}"
        )


@dataclass
class PlatformResult:
    """
    平台操作结果。
    """

    success: bool
    context: PlatformContext = field(default_factory=PlatformContext)
    audit_records: list[AuditRecord] = field(default_factory=list)
    error_message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
