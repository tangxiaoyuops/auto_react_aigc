"""Request schemas"""
from typing import List, Optional
from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    """Create session request"""
    title: Optional[str] = Field(None, description="Session title")
    model: str = Field(default="gpt-4o", description="Model to use")
    tools: List[str] = Field(default_factory=list, description="Enabled tools")
    skills: List[str] = Field(default_factory=list, description="Enabled skills")
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")


class SendMessageRequest(BaseModel):
    """Send message request"""
    content: str = Field(..., description="Message content")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")


class ExecuteAgentRequest(BaseModel):
    """Execute agent request"""
    run_id: str = Field(..., description="Run ID")
    session_id: str = Field(..., description="Session ID")
    message: str = Field(..., description="User message")
    model: str = Field(default="gpt-4o", description="Model to use")
    tools: List[str] = Field(default_factory=list, description="Available tools")
    system_prompt: Optional[str] = Field(None, description="System prompt")


class LoginRequest(BaseModel):
    """Login request"""
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")


class RegisterRequest(BaseModel):
    """Register request"""
    email: str = Field(..., description="User email")
    username: str = Field(..., description="Username")
    password: str = Field(..., min_length=8, description="Password (min 8 chars)")
