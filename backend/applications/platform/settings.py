from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class PlatformSettings(BaseSettings):
    """
    企业平台配置。
    """

    model_config = SettingsConfigDict(
        env_prefix="ENTERPRISE_PLATFORM_",
    )

    enable_platform: bool = Field(
        default=True,
        description="是否启用企业平台治理",
    )

    platform_data_root: Path = Field(
        default=Path("platform_data"),
        description="平台数据根目录",
    )

    default_organization_name: str = Field(
        default="Default Organization",
        description="默认组织名称",
    )

    default_workspace_name: str = Field(
        default="default",
        description="默认工作空间名称",
    )

    workspace_root: Path = Field(
        default=Path("workspace"),
        description="企业工作空间文件根目录",
    )

    default_model_provider: str = Field(
        default="openai",
        description="默认模型提供商",
    )

    default_model_id: str = Field(
        default="gpt-4o-mini",
        description="默认模型 ID",
    )

    audit_retention_days: int = Field(
        default=90,
        description="审计日志保留天数",
    )

    enforce_permissions: bool = Field(
        default=False,
        description="是否强制权限检查",
    )

    enforce_governance: bool = Field(
        default=True,
        description="是否启用治理策略检查",
    )
