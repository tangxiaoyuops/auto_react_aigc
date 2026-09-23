"""Event recorder for persisting run events

设计：事件持久化只依赖数据库，不依赖 Redis。
- sequence 序列号：查询当前 run 最大序列号 +1（避免 Redis 不可用导致事件丢失）
- 实时推送：由 SSEManager 广播完成，本模块只负责"仅追加"写入
"""
from typing import List, Optional
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import DBRunEvent


class EventRecorder:
    """Event recorder - append-only writes"""

    def __init__(self, db: AsyncSession, redis_client=None):
        self.db = db
        self.redis = redis_client  # 保留可选，不再必需

    async def record(
        self,
        run_id: str,
        session_id: str,
        event_type: str,
        content: dict,
        sequence: Optional[int] = None,
    ) -> DBRunEvent:
        """写入一个事件（追加）"""
        if sequence is None:
            sequence = await self._next_sequence(run_id)

        event = DBRunEvent(
            id=str(uuid4()),
            run_id=run_id,
            session_id=session_id,
            event_type=event_type,
            content=content,
            sequence=sequence,
            created_at=datetime.utcnow(),
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def _next_sequence(self, run_id: str) -> int:
        """基于数据库计算下一个序列号（幂等、不依赖 Redis）"""
        result = await self.db.execute(
            select(func.max(DBRunEvent.sequence)).where(DBRunEvent.run_id == run_id)
        )
        max_seq = result.scalar_one_or_none()
        return (max_seq or 0) + 1

    async def get_run_events(
        self,
        run_id: str,
        limit: int = 200,
        offset: int = 0,
    ) -> List[DBRunEvent]:
        """获取一个 run 的所有事件（按 sequence 升序）"""
        result = await self.db.execute(
            select(DBRunEvent)
            .where(DBRunEvent.run_id == run_id)
            .order_by(DBRunEvent.sequence)
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()