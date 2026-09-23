"""Message model"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from uuid import uuid4


class MessageRole(str, Enum):
    """Message role"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message:
    """Message model"""
    
    def __init__(
        self,
        id: str = None,
        session_id: str = None,
        role: MessageRole = MessageRole.USER,
        content: str = None,
        model: str = None,
        tokens_used: int = None,
        metadata: Dict[str, Any] = None,
        created_at: datetime = None
    ):
        self.id = id or str(uuid4())
        self.session_id = session_id
        self.role = role if isinstance(role, MessageRole) else MessageRole(role)
        self.content = content
        self.model = model
        self.tokens_used = tokens_used
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role.value,
            "content": self.content,
            "model": self.model,
            "tokens_used": self.tokens_used,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        """Create from dictionary"""
        return cls(
            id=data.get("id"),
            session_id=data.get("session_id"),
            role=MessageRole(data.get("role", "user")),
            content=data.get("content"),
            model=data.get("model"),
            tokens_used=data.get("tokens_used"),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
        )
