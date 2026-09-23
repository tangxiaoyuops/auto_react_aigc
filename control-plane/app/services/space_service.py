"""Space 服务：空间 + 成员管理"""
from typing import List, Optional
from uuid import uuid4
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.database import DBSpace, DBSpaceMember
from shared.schemas.space import SpaceCreate, SpaceUpdate, InviteMemberRequest


class SpaceService:
    """领域空间与成员管理"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------- Space ----------

    async def create_space(
        self, owner_id: str, payload: SpaceCreate, owner_account: str = None
    ) -> DBSpace:
        space = DBSpace(
            id=str(uuid4()),
            name=payload.name,
            description=payload.description,
            owner_id=owner_id,
            status="active",
            created_at=datetime.utcnow(),
        )
        self.db.add(space)
        await self.db.commit()
        await self.db.refresh(space)

        # 创建者自动成为管理员成员（account 用邮箱便于前端展示）
        await self.add_member(space.id, owner_id, owner_account or owner_id, "admin")
        return space

    async def list_spaces(self, user_id: str) -> List[DBSpace]:
        """用户参与的空间"""
        result = await self.db.execute(
            select(DBSpace)
            .join(DBSpaceMember, DBSpaceMember.space_id == DBSpace.id)
            .where(DBSpaceMember.user_id == user_id)
            .order_by(DBSpace.created_at.desc())
        )
        return result.scalars().all()

    async def get_space(self, space_id: str) -> Optional[DBSpace]:
        result = await self.db.execute(
            select(DBSpace).where(DBSpace.id == space_id)
        )
        return result.scalar_one_or_none()

    async def member_count(self, space_id: str) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(DBSpaceMember).where(
                DBSpaceMember.space_id == space_id,
                DBSpaceMember.status == "active",
            )
        )
        return result.scalar_one() or 0

    async def update_space(self, space: DBSpace, payload: SpaceUpdate) -> DBSpace:
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(space, field, value)
        space.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(space)
        return space

    # ---------- Members ----------

    async def list_members(self, space_id: str) -> List[DBSpaceMember]:
        result = await self.db.execute(
            select(DBSpaceMember)
            .where(DBSpaceMember.space_id == space_id)
            .order_by(DBSpaceMember.joined_at)
        )
        return result.scalars().all()

    async def add_member(
        self, space_id: str, user_id: str, account: str = None, role: str = "member",
        name: str = None, status: str = "active",
    ) -> DBSpaceMember:
        """添加/邀请成员（相同 account 幂等）"""
        result = await self.db.execute(
            select(DBSpaceMember).where(
                DBSpaceMember.space_id == space_id,
                DBSpaceMember.account == account,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        member = DBSpaceMember(
            id=str(uuid4()),
            space_id=space_id,
            user_id=user_id,
            name=name or (account or "").split("@")[0],
            account=account,
            role=role,
            status=status,
            joined_at=datetime.utcnow(),
        )
        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)
        return member

    async def invite_member(self, space_id: str, payload: InviteMemberRequest) -> DBSpaceMember:
        """邀请成员（新成员 user_id 暂用 uuid 占位，account 唯一）"""
        return await self.add_member(
            space_id=space_id,
            user_id=str(uuid4()),
            account=payload.account,
            name=payload.name or payload.account.split("@")[0],
            role=payload.role,
            status="active",
        )

    async def get_member(self, space_id: str, member_id: str) -> Optional[DBSpaceMember]:
        result = await self.db.execute(
            select(DBSpaceMember).where(
                DBSpaceMember.id == member_id,
                DBSpaceMember.space_id == space_id,
            )
        )
        return result.scalar_one_or_none()

    async def update_member(
        self, member: DBSpaceMember, role: str = None, status: str = None
    ) -> DBSpaceMember:
        if role is not None and role in ("admin", "member"):
            member.role = role
        if status is not None and status in ("active", "disabled"):
            member.status = status
        await self.db.commit()
        await self.db.refresh(member)
        return member