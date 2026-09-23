"""User model"""
from datetime import datetime
from typing import List
from uuid import uuid4


class User:
    """User model"""
    
    def __init__(
        self,
        id: str = None,
        email: str = None,
        username: str = None,
        password_hash: str = None,
        roles: List[str] = None,
        is_active: bool = True,
        created_at: datetime = None,
        updated_at: datetime = None
    ):
        self.id = id or str(uuid4())
        self.email = email
        self.username = username
        self.password_hash = password_hash
        self.roles = roles or ["user"]
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "roles": self.roles,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Create from dictionary"""
        return cls(
            id=data.get("id"),
            email=data.get("email"),
            username=data.get("username"),
            password_hash=data.get("password_hash"),
            roles=data.get("roles", ["user"]),
            is_active=data.get("is_active", True),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        )
