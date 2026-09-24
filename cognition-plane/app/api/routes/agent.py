"""Agent execution routes"""
import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional

from app.agent.engine import AgentEngine
from app.services.event_emitter import EventEmitter

router = APIRouter()


class ExecuteRequest(BaseModel):
    """Execute agent request"""
    run_id: str
    session_id: str
    message: str
    model: str = "gpt-4o"
    tools: List[str] = []
    skills: List[str] = []
    system_prompt: Optional[str] = None


@router.post("/execute")
async def execute_agent(request: ExecuteRequest):
    """Execute agent (synchronous)"""
    # Create agent
    agent = AgentEngine(
        model=request.model,
        tools=request.tools,
        skills=request.skills
    )
    
    # Execute
    result = await agent.run(
        message=request.message,
        system_prompt=request.system_prompt,
        thread_id=request.run_id
    )
    
    return {
        "run_id": request.run_id,
        "result": result
    }


@router.post("/execute/stream")
async def execute_agent_stream(request: ExecuteRequest):
    """Execute agent (streaming)"""
    # Create event emitter
    event_emitter = EventEmitter()
    
    # Create agent
    agent = AgentEngine(
        model=request.model,
        tools=request.tools,
        skills=request.skills,
        event_emitter=event_emitter
    )
    
    async def event_generator():
        """Generate SSE events"""
        # Start agent execution in background
        agent_task = asyncio.create_task(
            agent.run(
                message=request.message,
                system_prompt=request.system_prompt,
                thread_id=request.run_id
            )
        )
        
        # Stream events until agent finishes（EventEmitter 队列本身
        # 不会出现 RUN_END，需要轮询 agent 完成状态来结束循环）
        while not agent_task.done():
            try:
                event = await asyncio.wait_for(
                    event_emitter.event_queue.get(),
                    timeout=0.5,
                )
                yield f"data: {json.dumps(event)}\n\n"
            except asyncio.TimeoutError:
                continue
        
        # Wait for agent to complete
        try:
            result = await agent_task
            # Send final event
            yield f"data: {json.dumps({'type': 'RUN_END', 'data': {'result': result}})}\n\n"
        except Exception as e:
            # Send error event
            yield f"data: {json.dumps({'type': 'RUN_ERROR', 'data': {'error': str(e)}})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
