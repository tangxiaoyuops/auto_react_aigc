"""Session model"""
from datetime import datetime
from typing import List, Optional
from enum import Enum
from uuid import uuid4


class SessionStatus(str, Enum):
    """Session status"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Session:
    """Session model"""
    
    def __init__(
        self,
        id: str = None,
        user_id: str = None,
        title: str = None,
        model: str = "gpt-4o",
        tools: List[str] = None,
        skills: List[str] = None,
        system_prompt: str = None,
        status: SessionStatus = SessionStatus.ACTIVE,
        metadata: dict = None,
        created_at: datetime = None,
        updated_at: datetime = None
    ):
        self.id = id or str(uuid4())
        self.user_id = user_id
        self.title = title
        self.model = model
        self.tools = tools or []
        self.skills = skills or []
        self.system_prompt = system_prompt
        self.status = status
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "model": self.model,
            "tools": self.tools,
            "skills": self.skills,
            "system_prompt": self.system_prompt,
            "status": self.status.value if isinstance(self.status, SessionStatus) else self.status,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        """Create from dictionary"""
        return cls(
            id=data.get("id"),
            user_id=data.get("user_id"),
            title=data.get("title"),
            model=data.get("model", "gpt-4o"),
            tools=data.get("tools", []),
            skills=data.get("skills", []),
            system_prompt=data.get("system_prompt"),
            status=SessionStatus(data.get("status", "active")),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        )
