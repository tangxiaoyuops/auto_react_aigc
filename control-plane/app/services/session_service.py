"""Session service for managing sessions and runs

send_message 在请求线程内写入消息 + 创建 run，随后创建后台任务执行。
后台任务 _execute_run 新建独立的 AsyncSession，避免使用已关闭的请求 session。
"""
from typing import List, Optional
from uuid import uuid4
from datetime import datetime
import asyncio
import json

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import AsyncSessionLocal, DBMessage, DBSession, DBRun
from app.services.event_recorder import EventRecorder
from app.services.sse_manager import SSEManager
from app.services.sse_protocol import (
    error_event,
    result_event,
    run_end_event,
    run_start_event,
    thought_event,
    tool_call_end_event,
    tool_call_start_event,
)
from app.core.config import settings


class SessionService:
    """Session management service"""

    def __init__(
        self,
        db: AsyncSession,
        redis_client,
        sse_manager: SSEManager,
        event_recorder: EventRecorder = None,
    ):
        self.db = db
        self.redis = redis_client
        self.sse_manager = sse_manager
        self.event_recorder = event_recorder
        self.http_client = httpx.AsyncClient(timeout=300.0)

    # ---------- Session CRUD ----------

    async def create_session(
        self,
        user_id: str,
        title: str = None,
        model: str = "gpt-4o",
        tools: List[str] = None,
        skills: List[str] = None,
        system_prompt: str = None,
    ) -> DBSession:
        session = DBSession(
            id=str(uuid4()),
            user_id=user_id,
            title=title or f"Session {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            model=model,
            tools=tools or [],
            skills=skills or [],
            system_prompt=system_prompt,
            status="active",
            created_at=datetime.utcnow(),
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_session(self, session_id: str) -> Optional[DBSession]:
        result = await self.db.execute(
            select(DBSession).where(DBSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def list_sessions(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> List[DBSession]:
        offset = (page - 1) * page_size
        result = await self.db.execute(
            select(DBSession)
            .where(DBSession.user_id == user_id)
            .where(DBSession.status != "deleted")
            .order_by(DBSession.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        return result.scalars().all()

    # ---------- Run 启动 ----------

    async def send_message(
        self,
        session_id: str,
        user_id: str,
        content: str,
        agent: dict = None,
    ) -> DBRun:
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        if session.user_id != user_id:
            raise PermissionError("Not authorized to access this session")

        message = DBMessage(
            id=str(uuid4()),
            session_id=session_id,
            role="user",
            content=content,
            created_at=datetime.utcnow(),
        )
        self.db.add(message)

        run = DBRun(
            id=str(uuid4()),
            session_id=session_id,
            user_id=user_id,
            status="running",
            model=session.model,
            started_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            extra_data={"agent": agent} if agent else {},
        )
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)

        asyncio.create_task(self._execute_run(run_id=run.id, message_id=message.id))
        return run

    # ---------- 后台执行 ----------

    async def _execute_run(self, run_id: str, message_id: str):
        """后台执行 run：调用 Cognition Plane，回推 SSE 事件并持久化"""
        async with AsyncSessionLocal() as db:
            run = await self._get(db, DBRun, run_id)
            if not run:
                return
            message = await self._get(db, DBMessage, message_id)
            session = await self._get(db, DBSession, run.session_id)
            if not message or not session:
                return

            recorder = EventRecorder(db=db, redis_client=self.redis)
            await self._stream_from_cognition(db, run, session, message, recorder)

    @staticmethod
    async def _get(db: AsyncSession, model, obj_id: str):
        result = await db.execute(select(model).where(model.id == obj_id))
        return result.scalar_one_or_none()

    async def _stream_from_cognition(
        self,
        db: AsyncSession,
        run: DBRun,
        session: DBSession,
        message: DBMessage,
        recorder: EventRecorder,
    ):
        """调用 Cognition Plane 流式接口，逐事件转换并广播"""
        agent = (run.extra_data or {}).get("agent") if run.extra_data else None

        try:
            await self.sse_manager.broadcast(run.id, run_start_event(
                run_id=run.id,
                session_id=session.id,
                agent_id=(agent or {}).get("id"),
            ))
            await recorder.record(
                run_id=run.id, session_id=session.id,
                event_type="run_start",
                content={"run_id": run.id, "session_id": session.id},
            )

            async with self.http_client.stream(
                "POST",
                f"{settings.COGNITION_URL}/api/v1/agent/execute/stream",
                json={
                    "run_id": run.id,
                    "session_id": session.id,
                    "message": message.content,
                    "model": session.model,
                    "tools": session.tools or [],
                    "system_prompt": session.system_prompt,
                },
                timeout=300.0,
            ) as response:
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    raw = self._parse_json(line[6:])
                    if not raw:
                        continue
                    sse_event = self._to_trace_event(raw)
                    await recorder.record(
                        run_id=run.id, session_id=session.id,
                        event_type=sse_event["type"], content=sse_event["content"],
                    )
                    await self.sse_manager.broadcast(run.id, sse_event)

            run.status = "completed"
            run.completed_at = datetime.utcnow()
            await db.commit()

        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()
            await db.commit()
            await self.sse_manager.broadcast(run.id, error_event(str(e)))

    @staticmethod
    def _parse_json(text: str):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    # ---------- 事件协议转换（Trace Contract） ----------

    def _to_trace_event(self, raw: dict) -> dict:
        """将 Cognition Plane 原始事件转为前端 Step 结构"""
        event_type = raw.get("type", "")
        data = raw.get("data") or raw.get("content") or {}

        if event_type in ("REASONING_START", "REASONING_CONTENT", "REASONING_END"):
            return thought_event(
                node_name=data.get("node_name", "思考"),
                content=data.get("content", data.get("step", "") or ""),
            )
        if event_type == "TOOL_CALL_START":
            return tool_call_start_event(
                tool_name=data.get("tool_name", "tool"),
                input_json=data.get("tool_args", {}),
            )
        if event_type in ("TOOL_RESULT", "OBSERVATION"):
            return tool_call_end_event(
                tool_name=data.get("tool_name", "tool"),
                output_json=data.get("result", data.get("content", "")),
                duration_ms=int(data.get("duration_ms", 0) or 0),
            )
        if event_type == "TEXT_MESSAGE_CONTENT":
            content = data.get("content", "") or ""
            if content:
                return result_event(content=content)
            # 无内容则不产生 result 事件（避免空 detail 覆盖真正结果）
            return {"type": "noop", "content": {}}
        if event_type in ("TEXT_MESSAGE_START", "TEXT_MESSAGE_END"):
            # 生命周期标记，不含正文，忽略（防止产生空 result）
            return {"type": "noop", "content": {}}
        if event_type == "RUN_END":
            return run_end_event(
                run_id=data.get("run_id", ""),
                total_duration=int(data.get("total_duration", 0) or 0),
            )
        if event_type == "RUN_ERROR":
            return error_event(data.get("error", str(data)))
        return {"type": event_type.lower(), "content": data}

    async def get_run(self, run_id: str) -> Optional[DBRun]:
        result = await self.db.execute(select(DBRun).where(DBRun.id == run_id))
        return result.scalar_one_or_none()

    async def close(self):
        await self.http_client.aclose()