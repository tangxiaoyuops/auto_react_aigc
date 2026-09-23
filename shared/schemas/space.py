"""Space 相关 Schema（对应前端 workspace/index.tsx 领域空间 + 成员表格）"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class SpaceCreate(BaseModel):
    """创建空间请求"""
    name: str = Field(..., description="空间名称")
    description: Optional[str] = Field(None, description="空间描述")


class SpaceUpdate(BaseModel):
    """更新空间请求"""
    name: Optional[str] = None
    description: Optional[str] = None


class SpaceResponse(BaseModel):
    """空间响应"""
    id: str
    name: str
    description: Optional[str]
    owner_id: str
    status: str
    member_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class InviteMemberRequest(BaseModel):
    """邀请成员请求"""
    account: str = Field(..., description="被邀请人账号（邮箱）")
    name: Optional[str] = Field(None, description="展示名")
    role: str = Field("member", description="admin/member")


class MemberRoleUpdate(BaseModel):
    """成员角色/状态更新"""
    role: Optional[str] = None
    status: Optional[str] = None


class SpaceMemberResponse(BaseModel):
    """空间成员响应"""
    id: str
    space_id: str
    user_id: str
    name: Optional[str]
    account: Optional[str]
    role: str
    status: str
    joined_at: Optional[datetime]

    class Config:
        from_attributes = True