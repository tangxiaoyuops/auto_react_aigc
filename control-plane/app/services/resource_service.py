"""Resource 服务：5 类资源统一 CRUD"""
from typing import List, Optional
from uuid import uuid4
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import DBResource
from shared.schemas.resource import ResourceCreate, ResourceUpdate
from shared.schemas.skill_file import default_files


class ResourceService:
    """资源池管理"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_resource(self, user_id: str, payload: ResourceCreate) -> DBResource:
        meta = payload.meta or {}
        # Skill 资源：初始化默认文件树（与 Cursor 风格的 SKILL.md + 参考文件）
        if payload.type == "skill":
            files = meta.get("files")
            if not files:
                meta = {**meta, "files": default_files(payload.name, payload.description or "")}
        resource = DBResource(
            id=str(uuid4()),
            user_id=user_id,
            type=payload.type,
            name=payload.name,
            description=payload.description,
            meta=meta,
            origin="custom",
            created_at=datetime.utcnow(),
        )
        self.db.add(resource)
        await self.db.commit()
        await self.db.refresh(resource)
        # 把脚本同步到磁盘工作区（供 run_skill_script 执行）
        if payload.type == "skill":
            from app.services.skill_file_service import SkillFileStore
            SkillFileStore(db=self.db)._sync_scripts_to_disk(resource.id, resource.name, meta.get("files") or {})
        return resource

    async def list_resources(
        self,
        user_id: str,
        resource_type: str = None,
        keyword: str = None,
        page: int = 1,
        page_size: int = 50,
    ) -> List[DBResource]:
        query = select(DBResource).where(DBResource.user_id == user_id)
        if resource_type:
            query = query.where(DBResource.type == resource_type)
        if keyword:
            query = query.where(DBResource.name.like(f"%{keyword}%"))
        offset = (page - 1) * page_size
        query = query.order_by(DBResource.created_at.desc()).offset(offset).limit(page_size)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_resource(self, user_id: str, resource_id: str) -> Optional[DBResource]:
        result = await self.db.execute(
            select(DBResource).where(DBResource.id == resource_id, DBResource.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_resource(
        self, resource: DBResource, payload: ResourceUpdate
    ) -> DBResource:
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(resource, field, value)
        resource.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(resource)
        return resource

    async def delete_resource(self, resource: DBResource) -> None:
        if resource.type == "skill":
            from app.services.skill_file_service import SkillFileStore
            SkillFileStore(db=self.db).cleanup_skips(resource.name)
        await self.db.delete(resource)
        await self.db.commit()

    async def get_resources_by_ids(self, user_id: str, resource_ids: List[str]) -> List[DBResource]:
        """按 ID 批量取资源（Agent 挂载时展示名称等用）"""
        result = await self.db.execute(
            select(DBResource).where(
                DBResource.user_id == user_id, DBResource.id.in_(resource_ids)
            )
        )
        return result.scalars().all()