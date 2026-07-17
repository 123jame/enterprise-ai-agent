from __future__ import annotations

from datetime import datetime
from typing import Dict

from pydantic import BaseModel, Field


class Artifact(BaseModel):
    """
    软件开发产物。

    Artifact 表示软件开发过程中生成的任何成果，例如：

    - README
    - PRD
    - Architecture
    - Backend Code
    - Frontend Code
    - Test
    """

    id: str = Field(
        description="产物唯一ID"
    )

    name: str = Field(
        description="产物名称"
    )

    type: str = Field(
        description="产物类型"
    )

    path: str = Field(
        description="文件或目录路径"
    )

    owner: str = Field(
        description="生成该产物的Agent"
    )

    metadata: Dict[str, str] = Field(
        default_factory=dict,
        description="扩展信息"
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="创建时间"
    )