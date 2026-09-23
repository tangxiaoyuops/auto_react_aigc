"""Run model"""
from datetime import datetime
from typing import Optional
from enum import Enum
from uuid import uuid4


class RunStatus(str, Enum):
    """Run status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Run:
    """Run model"""
    
    def __init__(
        self,
        id: str = None,
        session_id: str = None,
        user_id: str = None,
        status: RunStatus = RunStatus.PENDING,
        model: str = None,
        total_tokens: int = 0,
        total_cost: float = 0.0,
        tool_calls_count: int = 0,
        reasoning_steps: int = 0,
        error_message: str = None,
        metadata: dict = None,
        started_at: datetime = None,
        completed_at: datetime = None,
        created_at: datetime = None
    ):
        self.id = id or str(uuid4())
        self.session_id = session_id
        self.user_id = user_id
        self.status = status if isinstance(status, RunStatus) else RunStatus(status)
        self.model = model
        self.total_tokens = total_tokens
        self.total_cost = total_cost
        self.tool_calls_count = tool_calls_count
        self.reasoning_steps = reasoning_steps
        self.error_message = error_message
        self.metadata = metadata or {}
        self.started_at = started_at
        self.completed_at = completed_at
        self.created_at = created_at or datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "status": self.status.value,
            "model": self.model,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "tool_calls_count": self.tool_calls_count,
            "reasoning_steps": self.reasoning_steps,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Run":
        """Create from dictionary"""
        return cls(
            id=data.get("id"),
            session_id=data.get("session_id"),
            user_id=data.get("user_id"),
            status=RunStatus(data.get("status", "pending")),
            model=data.get("model"),
            total_tokens=data.get("total_tokens", 0),
            total_cost=data.get("total_cost", 0.0),
            tool_calls_count=data.get("tool_calls_count", 0),
            reasoning_steps=data.get("reasoning_steps", 0),
            error_message=data.get("error_message"),
            metadata=data.get("metadata", {}),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
        )
