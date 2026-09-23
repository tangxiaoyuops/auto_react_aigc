"""Agent 相关 Schema（对应前端 Agent 列表/配置页）"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class AgentCreate(BaseModel):
    """创建 Agent 请求"""
    name: str = Field(..., description="Agent 名称")
    description: Optional[str] = Field(None, description="描述")
    space_id: Optional[str] = Field(None, description="所属空间 ID")
    model: str = Field("Qwen3.5-397b-a17b", description="底层大模型")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    avatar_color: str = Field("#1677ff", description="头像颜色")
    status: str = Field("draft", description="初始状态")
    temperature: float = Field(0.7, description="温度")
    max_iterations: int = Field(10, description="最大迭代")
    timeout: int = Field(300, description="超时秒数")
    greeting: Optional[str] = Field(None, description="欢迎语")
    suggestion_questions: List[str] = Field(default_factory=list, description="建议问题")
    knowledge_ids: List[str] = Field(default_factory=list, description="知识库资源 ID")
    ontology_ids: List[str] = Field(default_factory=list, description="本体资源 ID")
    skill_ids: List[str] = Field(default_factory=list, description="Skill 资源 ID")


class AgentUpdate(BaseModel):
    """更新 Agent 请求（全部可选，partial）"""
    name: Optional[str] = None
    description: Optional[str] = None
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    avatar_color: Optional[str] = None
    status: Optional[str] = None
    temperature: Optional[float] = None
    max_iterations: Optional[int] = None
    timeout: Optional[int] = None
    greeting: Optional[str] = None
    suggestion_questions: Optional[List[str]] = None
    knowledge_ids: Optional[List[str]] = None
    ontology_ids: Optional[List[str]] = None
    skill_ids: Optional[List[str]] = None


class AgentAttachRequest(BaseModel):
    """挂载能力资源请求"""
    resource_type: str = Field(..., description="knowledge/ontology/skill")
    resource_ids: List[str] = Field(..., description="资源 ID 列表")


class AgentResponse(BaseModel):
    """Agent 响应"""
    id: str
    name: str
    description: Optional[str]
    space_id: Optional[str]
    model: str
    system_prompt: Optional[str]
    avatar_color: str
    status: str
    version: int
    temperature: float
    max_iterations: int
    timeout: int
    greeting: Optional[str]
    suggestion_questions: List[str]
    knowledge_ids: List[str]
    ontology_ids: List[str]
    skill_ids: List[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
