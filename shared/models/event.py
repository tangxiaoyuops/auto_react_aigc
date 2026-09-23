"""Event model"""
from datetime import datetime
from typing import Dict, Any
from enum import Enum
from uuid import uuid4


class EventType(str, Enum):
    """Event types"""
    # Reasoning
    THOUGHT = "THOUGHT"
    REASONING_START = "REASONING_START"
    REASONING_CONTENT = "REASONING_CONTENT"
    REASONING_END = "REASONING_END"
    
    # Tool calls
    TOOL_CALL_START = "TOOL_CALL_START"
    TOOL_CALL_ARGS = "TOOL_CALL_ARGS"
    TOOL_CALL_END = "TOOL_CALL_END"
    TOOL_RESULT = "TOOL_RESULT"
    
    # Messages
    TEXT_MESSAGE_START = "TEXT_MESSAGE_START"
    TEXT_MESSAGE_CONTENT = "TEXT_MESSAGE_CONTENT"
    TEXT_MESSAGE_END = "TEXT_MESSAGE_END"
    
    # Observation
    OBSERVATION = "OBSERVATION"
    
    # Run status
    RUN_START = "RUN_START"
    RUN_END = "RUN_END"
    RUN_ERROR = "RUN_ERROR"
    
    # Human-in-the-loop
    HITL_REQUEST = "HITL_REQUEST"
    HITL_RESPONSE = "HITL_RESPONSE"


class RunEvent:
    """Run event model"""
    
    def __init__(
        self,
        id: str = None,
        run_id: str = None,
        session_id: str = None,
        event_type: EventType = None,
        content: Dict[str, Any] = None,
        sequence: int = 0,
        created_at: datetime = None
    ):
        self.id = id or str(uuid4())
        self.run_id = run_id
        self.session_id = session_id
        self.event_type = event_type if isinstance(event_type, EventType) else EventType(event_type) if event_type else None
        self.content = content or {}
        self.sequence = sequence
        self.created_at = created_at or datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "run_id": self.run_id,
            "session_id": self.session_id,
            "event_type": self.event_type.value if self.event_type else None,
            "content": self.content,
            "sequence": self.sequence,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "RunEvent":
        """Create from dictionary"""
        return cls(
            id=data.get("id"),
            run_id=data.get("run_id"),
            session_id=data.get("session_id"),
            event_type=EventType(data.get("event_type")) if data.get("event_type") else None,
            content=data.get("content", {}),
            sequence=data.get("sequence", 0),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
        )
