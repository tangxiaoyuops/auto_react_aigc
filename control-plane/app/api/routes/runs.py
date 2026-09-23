"""Run routes"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.db.database import get_db, DBRun
from app.core.security import get_current_user, TokenPayload
from shared.schemas.responses import RunResponse

router = APIRouter()


class RunListResponse(BaseModel):
    """Run list response"""
    runs: List[RunResponse]
    total: int


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get run by ID"""
    result = await db.execute(
        select(DBRun).where(DBRun.id == run_id)
    )
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    if run.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return RunResponse(
        id=run.id,
        session_id=run.session_id,
        user_id=run.user_id,
        status=run.status,
        model=run.model,
        total_tokens=run.total_tokens,
        tool_calls_count=run.tool_calls_count,
        started_at=run.started_at,
        completed_at=run.completed_at,
        created_at=run.created_at
    )


@router.get("/{run_id}/stream")
async def stream_run_events(
    run_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Stream run events via SSE"""
    from app.main import app
    
    # Verify access
    result = await db.execute(
        select(DBRun).where(DBRun.id == run_id)
    )
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    if run.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Connect to SSE manager
    sse_manager = app.state.sse_manager
    queue = await sse_manager.connect(run_id)
    
    return StreamingResponse(
        sse_manager.stream_response(run_id, queue),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("", response_model=RunListResponse)
async def list_runs(
    session_id: str = None,
    status: str = None,
    limit: int = 20,
    offset: int = 0,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List runs"""
    query = select(DBRun).where(DBRun.user_id == current_user.user_id)
    
    if session_id:
        query = query.where(DBRun.session_id == session_id)
    
    if status:
        query = query.where(DBRun.status == status)
    
    query = query.order_by(DBRun.created_at.desc()).offset(offset).limit(limit)
    
    result = await db.execute(query)
    runs = result.scalars().all()
    
    return RunListResponse(
        runs=[
            RunResponse(
                id=r.id,
                session_id=r.session_id,
                user_id=r.user_id,
                status=r.status,
                model=r.model,
                total_tokens=r.total_tokens,
                tool_calls_count=r.tool_calls_count,
                started_at=r.started_at,
                completed_at=r.completed_at,
                created_at=r.created_at
            )
            for r in runs
        ],
        total=len(runs)
    )


@router.delete("/{run_id}")
async def cancel_run(
    run_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel run"""
    result = await db.execute(
        select(DBRun).where(DBRun.id == run_id)
    )
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    if run.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if run.status != "running":
        raise HTTPException(status_code=400, detail="Can only cancel running tasks")
    
    # Cancel run
    run.status = "cancelled"
    await db.commit()
    
    # Broadcast cancellation event
    from app.main import app
    await app.state.sse_manager.broadcast(run_id, {
        "type": "RUN_CANCELLED",
        "content": {"message": "Run cancelled by user"}
    })
    
    return {"message": "Run cancelled"}
