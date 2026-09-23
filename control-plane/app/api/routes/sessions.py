"""Session routes"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.db.database import get_db, DBSession, DBRun, DBRunEvent
from app.core.security import get_current_user, TokenPayload
from app.services.session_service import SessionService
from app.services.sse_manager import SSEManager
from app.services.sse_protocol import TERMINAL_EVENTS
from shared.schemas.requests import CreateSessionRequest
from shared.schemas.responses import SessionResponse

router = APIRouter()


class SessionListResponse(BaseModel):
    """Session list response"""
    sessions: List[SessionResponse]
    total: int
    page: int
    page_size: int


class RunStartRequest(BaseModel):
    """发送消息并创建 Run 请求"""
    content: str = Field(..., description="用户消息")
    agent: Optional[dict] = Field(None, description="Agent 配置快照（调试时随消息携带）")


def get_session_service(
    db: AsyncSession = Depends(get_db),
) -> SessionService:
    """Get session service"""
    from app.main import app
    return SessionService(
        db=db,
        redis_client=app.state.redis,
        sse_manager=app.state.sse_manager,
        event_recorder=app.state.event_recorder
    )


@router.post("", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest,
    current_user: TokenPayload = Depends(get_current_user),
    service: SessionService = Depends(get_session_service)
):
    """Create new session"""
    session = await service.create_session(
        user_id=current_user.user_id,
        title=request.title,
        model=request.model,
        tools=request.tools,
        skills=request.skills,
        system_prompt=request.system_prompt
    )
    
    return SessionResponse(
        id=session.id,
        user_id=session.user_id,
        title=session.title,
        model=session.model,
        tools=session.tools,
        skills=session.skills,
        status=session.status,
        created_at=session.created_at,
        updated_at=session.updated_at
    )


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    page: int = 1,
    page_size: int = 20,
    current_user: TokenPayload = Depends(get_current_user),
    service: SessionService = Depends(get_session_service)
):
    """List user's sessions"""
    sessions = await service.list_sessions(
        user_id=current_user.user_id,
        page=page,
        page_size=page_size
    )
    
    return SessionListResponse(
        sessions=[
            SessionResponse(
                id=s.id,
                user_id=s.user_id,
                title=s.title,
                model=s.model,
                tools=s.tools,
                skills=s.skills,
                status=s.status,
                created_at=s.created_at,
                updated_at=s.updated_at
            )
            for s in sessions
        ],
        total=len(sessions),  # Simplified, should get actual count
        page=page,
        page_size=page_size
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    service: SessionService = Depends(get_session_service)
):
    """Get session by ID"""
    session = await service.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return SessionResponse(
        id=session.id,
        user_id=session.user_id,
        title=session.title,
        model=session.model,
        tools=session.tools,
        skills=session.skills,
        status=session.status,
        created_at=session.created_at,
        updated_at=session.updated_at
    )


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    service: SessionService = Depends(get_session_service)
):
    """Delete session"""
    session = await service.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Soft delete
    session.status = "deleted"
    await service.db.commit()
    
    return {"message": "Session deleted"}


# ======================= Run 入口（P0） =======================

@router.post("/{session_id}/runs")
async def start_run(
    session_id: str,
    request: RunStartRequest,
    current_user: TokenPayload = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
):
    """发送消息并启动 Run（前端 '发送' 按钮）

    返回 run 信息，前端随后通过 GET /{session_id}/stream 订阅 SSE
    """
    try:
        run = await service.send_message(
            session_id=session_id,
            user_id=current_user.user_id,
            content=request.content,
            agent=request.agent,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    return {
        "run_id": run.id,
        "session_id": session_id,
        "status": run.status,
        "message": "Run started, subscribe to /stream for events",
    }


@router.get("/{session_id}/stream")
async def stream_session_events(
    session_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """SSE 实时事件流（前端 DebugPanel / 对话页订阅）

    通过 run 订阅：前端拿到 run_id 后连到这个流。
    为兼容前端一次连接体验，这里支持按 run_id 过滤。
    """
    from app.main import app

    # 校验会话权限
    result = await db.execute(
        select(DBSession).where(DBSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    sse_manager: SSEManager = app.state.sse_manager

    # 如果指定 run_id 参数则只订阅该 run
    # 简化：订阅该 session 下最新一个 run（前端当前只调试一个 run）
    run_result = await db.execute(
        select(DBRun)
        .where(DBRun.session_id == session_id)
        .order_by(DBRun.created_at.desc())
        .limit(1)
    )
    latest_run = run_result.scalar_one_or_none()
    if not latest_run:
        raise HTTPException(status_code=404, detail="No runs found for session")

    queue = await sse_manager.connect(latest_run.id)

    return StreamingResponse(
        sse_manager.stream_response(latest_run.id, queue),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{session_id}/runs/{run_id}/events")
async def get_run_events(
    session_id: str,
    run_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run 事件历史重放（前端 Trace 详情 / 历史记录）"""
    from app.main import app
    from app.services.event_recorder import EventRecorder

    # 校验权限
    result = await db.execute(
        select(DBRun).where(DBRun.id == run_id, DBRun.session_id == session_id)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # 按需创建 recorder（使用当前请求的 db session）
    recorder = EventRecorder(db=db, redis_client=app.state.redis)
    events = await recorder.get_run_events(run_id)
    return {
        "run_id": run_id,
        "events": [
            {
                "type": e.event_type,
                "content": e.content,
                "sequence": e.sequence,
                "created_at": e.created_at,
            }
            for e in events
        ],
    }
