"""Base models with common mixins"""
from datetime import datetime
from typing import Optional


class TimestampMixin:
    """Timestamp mixin for models"""
    
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    def touch(self):
        """Update timestamp"""
        self.updated_at = datetime.utcnow()
