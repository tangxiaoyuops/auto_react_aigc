"""Response schemas"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class SessionResponse(BaseModel):
    """Session response"""
    id: str
    user_id: str
    title: Optional[str]
    model: str
    tools: List[str]
    skills: List[str]
    status: str
    created_at: datetime
    updated_at: Optional[datetime]


class MessageResponse(BaseModel):
    """Message response"""
    id: str
    session_id: str
    role: str
    content: str
    model: Optional[str]
    tokens_used: Optional[int]
    created_at: datetime


class RunResponse(BaseModel):
    """Run response"""
    id: str
    session_id: str
    user_id: str
    status: str
    model: Optional[str]
    total_tokens: int
    tool_calls_count: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: str
    status_code: int


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
