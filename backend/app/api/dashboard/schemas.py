from pydantic import BaseModel
from pydantic import Field


class CreateProjectRequest(BaseModel):

    requirement: str = Field(..., min_length=1, description="用户需求")
    project_name: str | None = Field(default=None, description="项目名称")
    user_id: str = Field(default="dashboard", description="发起用户")


class CreateProjectResponse(BaseModel):

    session_id: str
    project_id: str
    name: str
    requirement: str
    status: str
