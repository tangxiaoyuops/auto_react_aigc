"""Resource 相关 Schema（对应前端资源库 5 个 Tab）"""
from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


# 资源类型（与前端 TabKey 对齐；tool 为第 6 类：前端可配置工具）
RESOURCE_TYPES = ["kb", "skill", "prompt", "ontology", "ds", "tool"]


class ResourceCreate(BaseModel):
    """创建资源请求"""
    type: str = Field(..., description="kb/skill/prompt/ontology/ds")
    name: str = Field(..., description="资源名称")
    description: Optional[str] = Field(None, description="资源描述")
    meta: Optional[dict] = Field(default_factory=dict, description="元信息（版本/文档数/接入状态）")


class ResourceUpdate(BaseModel):
    """更新资源请求（partial）"""
    name: Optional[str] = None
    description: Optional[str] = None
    meta: Optional[dict] = None


class ResourceResponse(BaseModel):
    """资源响应"""
    id: str
    type: str
    name: str
    description: Optional[str]
    meta: Any
    origin: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True