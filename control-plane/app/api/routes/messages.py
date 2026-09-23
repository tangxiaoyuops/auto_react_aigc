"""Message routes"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.db.database import get_db, DBMessage
from app.core.security import get_current_user, TokenPayload
from shared.schemas.requests import SendMessageRequest
from shared.schemas.responses import MessageResponse

router = APIRouter()


class MessageListResponse(BaseModel):
    """Message list response"""
    messages: List[MessageResponse]
    total: int


@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send message to session"""
    from app.main import app
    from app.services.session_service import SessionService
    
    service = SessionService(
        db=db,
        redis_client=app.state.redis,
        sse_manager=app.state.sse_manager,
        event_recorder=app.state.event_recorder
    )
    
    # This will also create a run
    run = await service.send_message(
        session_id=session_id,
        user_id=current_user.user_id,
        content=request.content
    )
    
    # Return the user message
    result = await db.execute(
        select(DBMessage)
        .where(DBMessage.session_id == session_id)
        .order_by(DBMessage.created_at.desc())
        .limit(1)
    )
    message = result.scalar_one()
    
    return MessageResponse(
        id=message.id,
        session_id=message.session_id,
        role=message.role,
        content=message.content,
        model=message.model,
        tokens_used=message.tokens_used,
        created_at=message.created_at
    )


@router.get("/sessions/{session_id}/messages", response_model=MessageListResponse)
async def list_messages(
    session_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """List session messages"""
    # Verify access
    from app.db.database import DBSession
    session_result = await db.execute(
        select(DBSession).where(DBSession.id == session_id)
    )
    session = session_result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get messages
    result = await db.execute(
        select(DBMessage)
        .where(DBMessage.session_id == session_id)
        .order_by(DBMessage.created_at)
        .offset(offset)
        .limit(limit)
    )
    messages = result.scalars().all()
    
    return MessageListResponse(
        messages=[
            MessageResponse(
                id=m.id,
                session_id=m.session_id,
                role=m.role,
                content=m.content,
                model=m.model,
                tokens_used=m.tokens_used,
                created_at=m.created_at
            )
            for m in messages
        ],
        total=len(messages)
    )
