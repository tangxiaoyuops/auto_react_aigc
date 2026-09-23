"""Evaluation 相关 Schema（对应前端 evaluation/index.tsx 评测中心）"""
from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class DatasetCreate(BaseModel):
    """新建评测集"""
    name: str = Field(..., description="评测集名称")
    description: Optional[str] = Field(None, description="描述")


class CaseCreate(BaseModel):
    """新增评测用例"""
    question: str = Field(..., description="问题")
    expected: str = Field("", description="期望答案")


class CaseUpdate(BaseModel):
    """更新评测用例"""
    question: Optional[str] = None
    expected: Optional[str] = None


class DatasetResponse(BaseModel):
    """评测集响应"""
    id: str
    name: str
    description: Optional[str]
    case_count: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class CaseResponse(BaseModel):
    """评测用例响应"""
    id: str
    dataset_id: str
    question: str
    expected: str
    actual: Optional[str]
    score: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    """创建评测任务"""
    name: str = Field(..., description="任务名称")
    agent_id: Optional[str] = Field(None, description="评测的 Agent ID")
    agent_name: Optional[str] = Field(None, description="Agent 名称")
    dataset_id: str = Field(..., description="评测集 ID")


class TaskResponse(BaseModel):
    """评测任务响应"""
    id: str
    name: str
    agent_id: Optional[str]
    agent_name: Optional[str]
    dataset_id: Optional[str]
    status: str
    progress: int
    total_cases: int
    passed_cases: int
    report: Any
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True