"""Agent 路由：CRUD + 状态机 + 能力关联"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.core.security import get_current_user, TokenPayload
from app.services.agent_service import AgentService
from shared.schemas.agent import (
    AgentCreate, AgentUpdate, AgentAttachRequest, AgentResponse,
)

router = APIRouter()


def get_agent_service(db: AsyncSession = Depends(get_db)) -> AgentService:
    return AgentService(db=db)


def _serialize(agent) -> AgentResponse:
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        space_id=agent.space_id,
        model=agent.model,
        system_prompt=agent.system_prompt,
        avatar_color=agent.avatar_color,
        status=agent.status,
        version=agent.version,
        temperature=agent.temperature,
        max_iterations=agent.max_iterations,
        timeout=agent.timeout,
        greeting=agent.greeting,
        suggestion_questions=agent.suggestion_questions or [],
        knowledge_ids=agent.knowledge_ids or [],
        ontology_ids=agent.ontology_ids or [],
        skill_ids=agent.skill_ids or [],
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )


@router.post("", response_model=AgentResponse)
async def create_agent(
    payload: AgentCreate,
    current_user: TokenPayload = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
):
    """创建 Agent"""
    agent = await service.create_agent(user_id=current_user.user_id, payload=payload)
    return _serialize(agent)


@router.get("", response_model=dict)
async def list_agents(
    keyword: str = None,
    status: str = None,
    space_id: str = None,
    page: int = 1,
    page_size: int = 20,
    current_user: TokenPayload = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
):
    """Agent 列表（支持搜索/筛选/分页）"""
    agents = await service.list_agents(
        user_id=current_user.user_id,
        keyword=keyword,
        status=status,
        space_id=space_id,
        page=page,
        page_size=page_size,
    )
    total = await service.count_agents(user_id=current_user.user_id, status=status)
    return {
        "agents": [_serialize(a) for a in agents],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/stats", response_model=dict)
async def agent_stats(
    current_user: TokenPayload = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
):
    """Agent 统计（列表页顶部卡片）"""
    return {
        "total": await service.count_agents(current_user.user_id),
        "published": await service.count_agents(current_user.user_id, "published"),
        "draft": await service.count_agents(current_user.user_id, "draft"),
    }


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
):
    """获取单个 Agent"""
    agent = await service.get_agent(current_user.user_id, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return _serialize(agent)


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    payload: AgentUpdate,
    current_user: TokenPayload = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
):
    """更新 Agent（partial）"""
    agent = await service.get_agent(current_user.user_id, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent = await service.update_agent(agent, payload)
    return _serialize(agent)


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
):
    """删除 Agent"""
    agent = await service.get_agent(current_user.user_id, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    await service.delete_agent(agent)
    return {"message": "Agent deleted"}


@router.post("/{agent_id}/publish", response_model=AgentResponse)
async def publish_agent(
    agent_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
):
    """上架 Agent（draft -> published）"""
    agent = await service.get_agent(current_user.user_id, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    try:
        agent = await service.transition_status(agent, "published")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _serialize(agent)


@router.post("/{agent_id}/unpublish", response_model=AgentResponse)
async def unpublish_agent(
    agent_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
):
    """下架 Agent（published -> draft）"""
    agent = await service.get_agent(current_user.user_id, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    try:
        agent = await service.transition_status(agent, "draft")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _serialize(agent)


@router.post("/{agent_id}/capabilities", response_model=AgentResponse)
async def attach_capabilities(
    agent_id: str,
    payload: AgentAttachRequest,
    current_user: TokenPayload = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
):
    """挂载能力资源（知识库/本体/Skill）"""
    agent = await service.get_agent(current_user.user_id, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    try:
        agent = await service.attach_resources(
            agent, payload.resource_type, payload.resource_ids
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _serialize(agent)
