"""Agent 服务：CRUD + 状态机 + 能力关联"""
from typing import List, Optional
from uuid import uuid4
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import DBAgent, DBAgentVersion
from shared.schemas.agent import AgentCreate, AgentUpdate


class AgentService:
    """Agent 配置的管理服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------- CRUD ----------

    async def create_agent(self, user_id: str, payload: AgentCreate) -> DBAgent:
        agent = DBAgent(
            id=str(uuid4()),
            user_id=user_id,
            space_id=payload.space_id,
            name=payload.name,
            description=payload.description,
            model=payload.model,
            system_prompt=payload.system_prompt,
            prompt_resource_id=payload.prompt_resource_id,
            avatar_color=payload.avatar_color,
            status=payload.status or "draft",
            version=1,
            temperature=payload.temperature,
            max_iterations=payload.max_iterations,
            timeout=payload.timeout,
            greeting=payload.greeting,
            suggestion_questions=payload.suggestion_questions or [],
            knowledge_ids=payload.knowledge_ids or [],
            ontology_ids=payload.ontology_ids or [],
            skill_ids=payload.skill_ids or [],
            tool_ids=payload.tool_ids or [],
            created_at=datetime.utcnow(),
        )
        self.db.add(agent)
        await self.db.commit()
        await self.db.refresh(agent)
        return agent

    async def list_agents(
        self,
        user_id: str,
        keyword: str = None,
        status: str = None,
        space_id: str = None,
        page: int = 1,
        page_size: int = 20,
    ) -> List[DBAgent]:
        query = select(DBAgent).where(DBAgent.user_id == user_id)
        if status:
            query = query.where(DBAgent.status == status)
        if space_id:
            query = query.where(DBAgent.space_id == space_id)
        if keyword:
            query = query.where(DBAgent.name.like(f"%{keyword}%"))
        offset = (page - 1) * page_size
        query = query.order_by(DBAgent.created_at.desc()).offset(offset).limit(page_size)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def count_agents(self, user_id: str, status: str = None) -> int:
        query = select(DBAgent).where(DBAgent.user_id == user_id)
        if status:
            query = query.where(DBAgent.status == status)
        result = await self.db.execute(query)
        return len(result.scalars().all())

    async def get_agent(self, user_id: str, agent_id: str) -> Optional[DBAgent]:
        result = await self.db.execute(
            select(DBAgent).where(DBAgent.id == agent_id, DBAgent.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_agent(self, agent: DBAgent, payload: AgentUpdate) -> DBAgent:
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(agent, field, value)
        agent.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(agent)
        return agent

    async def delete_agent(self, agent: DBAgent) -> None:
        await self.db.delete(agent)
        await self.db.commit()

    # ---------- 状态机 ----------

    async def transition_status(self, agent: DBAgent, to_status: str) -> DBAgent:
        """Agent 状态机：draft -> published -> archived，发布时打版本快照"""
        allowed = {
            "draft": ["published", "archived"],
            "published": ["draft", "archived"],
            "archived": ["draft"],
        }
        if to_status not in allowed.get(agent.status, []):
            raise ValueError(f"非法状态流转: {agent.status} -> {to_status}")

        if to_status == "published" and agent.status != "published":
            # 每次上架生成新版本
            agent.version = (agent.version or 0) + 1
            snapshot = {
                field: getattr(agent, field)
                for field in ("name", "description", "model", "system_prompt",
                              "temperature", "max_iterations", "timeout",
                              "knowledge_ids", "ontology_ids", "skill_ids")
            }
            self.db.add(DBAgentVersion(
                id=str(uuid4()),
                agent_id=agent.id,
                version=agent.version,
                snapshot=snapshot,
                status="published",
                published_by=agent.user_id,
                created_at=datetime.utcnow(),
            ))

        agent.status = to_status
        agent.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(agent)
        return agent

    # ---------- 能力关联 ----------

    async def attach_resources(
        self, agent: DBAgent, resource_type: str, resource_ids: List[str]
    ) -> DBAgent:
        """挂载资源（knowledge/ontology/skill）"""
        field_map = {
            "knowledge": "knowledge_ids",
            "ontology": "ontology_ids",
            "skill": "skill_ids",
            "tool": "tool_ids",
        }
        field = field_map.get(resource_type)
        if not field:
            raise ValueError(f"未知能力类型: {resource_type}")
        setattr(agent, field, resource_ids)
        agent.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(agent)
        return agent

    # ---------- RunSpec 装配 ----------

    async def compile_runspec(self, agent: DBAgent) -> dict:
        """把 Agent 配置编译为可执行 RunSpec（配置态 -> 运行态）。

        - system_prompt：若引用 prompt 资源（prompt_resource_id），
          优先取资源 meta.content；否则用 Agent 内联 system_prompt。
        - tools：直接取 tool_ids；skill 携带的工具由认知层 loader 补齐。
        - skills：skill_ids 透传。
        """
        from shared.schemas.runspec import RunSpec
        from app.db.database import DBResource
        from sqlalchemy import select

        system_prompt = agent.system_prompt or ""
        if agent.prompt_resource_id:
            res = (await self.db.execute(
                select(DBResource).where(
                    DBResource.id == agent.prompt_resource_id,
                    DBResource.user_id == agent.user_id,
                )
            )).scalar_one_or_none()
            if res:
                content = (res.meta or {}).get("content")
                if content:
                    system_prompt = content

        return RunSpec(
            agent_id=agent.id,
            name=agent.name,
            model=agent.model,
            system_prompt=system_prompt,
            tools=agent.tool_ids or [],
            skills=agent.skill_ids or [],
            knowledge=[
                {"resource_id": kid, "name": "", "top_k": 5}
                for kid in (agent.knowledge_ids or [])
            ],
            temperature=agent.temperature,
            max_iterations=agent.max_iterations,
            timeout=agent.timeout,
        ).model_dump()
