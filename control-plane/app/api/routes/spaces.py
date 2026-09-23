"""Space 路由：领域空间 + 成员管理"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.core.security import get_current_user, TokenPayload
from app.services.space_service import SpaceService
from shared.schemas.space import (
    SpaceCreate, SpaceUpdate, SpaceResponse,
    InviteMemberRequest, MemberRoleUpdate, SpaceMemberResponse,
)

router = APIRouter()


def get_space_service(db: AsyncSession = Depends(get_db)) -> SpaceService:
    return SpaceService(db=db)


def _serialize_space(s, member_count: int) -> dict:
    return {
        "id": s.id,
        "name": s.name,
        "description": s.description,
        "owner_id": s.owner_id,
        "status": s.status,
        "member_count": member_count,
        "created_at": s.created_at,
        "updated_at": s.updated_at,
    }


def _serialize_member(m) -> SpaceMemberResponse:
    return SpaceMemberResponse(
        id=m.id,
        space_id=m.space_id,
        user_id=m.user_id,
        name=m.name,
        account=m.account,
        role=m.role,
        status=m.status,
        joined_at=m.joined_at,
    )


@router.get("/me")
async def get_my_spaces(
    current_user: TokenPayload = Depends(get_current_user),
    service: SpaceService = Depends(get_space_service),
):
    """"返回领域空间"（顶栏）：列出当前用户参与的空间"""
    spaces = await service.list_spaces(current_user.user_id)
    return {
        "spaces": [
            _serialize_space(s, await service.member_count(s.id))
            for s in spaces
        ],
    }


@router.get("", response_model=dict)
async def list_spaces(
    current_user: TokenPayload = Depends(get_current_user),
    service: SpaceService = Depends(get_space_service),
):
    spaces = await service.list_spaces(current_user.user_id)
    return {
        "spaces": [
            _serialize_space(s, await service.member_count(s.id))
            for s in spaces
        ],
    }


@router.post("", response_model=dict)
async def create_space(
    payload: SpaceCreate,
    current_user: TokenPayload = Depends(get_current_user),
    service: SpaceService = Depends(get_space_service),
):
    """创建空间（创建者自动成为 admin，account 用用户邮箱）"""
    space = await service.create_space(
        owner_id=current_user.user_id, payload=payload, owner_account=current_user.email
    )
    result = _serialize_space(space, await service.member_count(space.id))
    members = await service.list_members(space.id)
    result["members"] = [_serialize_member(m) for m in members]
    return result


@router.get("/{space_id}", response_model=dict)
async def get_space(
    space_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    service: SpaceService = Depends(get_space_service),
):
    space = await service.get_space(space_id)
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    return _serialize_space(space, await service.member_count(space.id))


@router.put("/{space_id}", response_model=dict)
async def update_space(
    space_id: str,
    payload: SpaceUpdate,
    current_user: TokenPayload = Depends(get_current_user),
    service: SpaceService = Depends(get_space_service),
):
    space = await service.get_space(space_id)
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    if space.owner_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Only owner can update space")
    space = await service.update_space(space, payload)
    return _serialize_space(space, await service.member_count(space.id))


@router.get("/{space_id}/members", response_model=dict)
async def list_members(
    space_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    service: SpaceService = Depends(get_space_service),
):
    """空间成员表格数据"""
    space = await service.get_space(space_id)
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    members = await service.list_members(space_id)
    return {
        "members": [_serialize_member(m) for m in members],
        "total": len(members),
    }


@router.post("/{space_id}/members/invite", response_model=SpaceMemberResponse)
async def invite_member(
    space_id: str,
    payload: InviteMemberRequest,
    current_user: TokenPayload = Depends(get_current_user),
    service: SpaceService = Depends(get_space_service),
):
    """邀请成员"""
    space = await service.get_space(space_id)
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    member = await service.invite_member(space_id, payload)
    return _serialize_member(member)


@router.put("/{space_id}/members/{member_id}", response_model=SpaceMemberResponse)
async def update_member(
    space_id: str,
    member_id: str,
    payload: MemberRoleUpdate,
    current_user: TokenPayload = Depends(get_current_user),
    service: SpaceService = Depends(get_space_service),
):
    """停用/启用成员、改角色"""
    member = await service.get_member(space_id, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member = await service.update_member(
        member, role=payload.role, status=payload.status
    )
    return _serialize_member(member)