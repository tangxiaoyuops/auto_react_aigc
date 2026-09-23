"""Resource 路由：5 类资源统一 CRUD"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.core.security import get_current_user, TokenPayload
from app.services.resource_service import ResourceService
from shared.schemas.resource import (
    RESOURCE_TYPES, ResourceCreate, ResourceUpdate, ResourceResponse,
)

router = APIRouter()


def get_resource_service(db: AsyncSession = Depends(get_db)) -> ResourceService:
    return ResourceService(db=db)


def _serialize(r) -> ResourceResponse:
    return ResourceResponse(
        id=r.id,
        type=r.type,
        name=r.name,
        description=r.description,
        meta=r.meta or {},
        origin=r.origin,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


@router.get("", response_model=dict)
async def list_resources(
    type: str = None,
    keyword: str = None,
    page: int = 1,
    page_size: int = 50,
    current_user: TokenPayload = Depends(get_current_user),
    service: ResourceService = Depends(get_resource_service),
):
    """资源列表（前端 5 个 Tab 用 ?type=kb|skill|prompt|ontology|ds 过滤）"""
    if type and type not in RESOURCE_TYPES:
        raise HTTPException(status_code=400, detail=f"非法资源类型: {type}，可选: {RESOURCE_TYPES}")
    resources = await service.list_resources(
        user_id=current_user.user_id,
        resource_type=type,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )
    return {
        "resources": [_serialize(r) for r in resources],
        "total": len(resources),
        "type": type,
    }


@router.get("/pool", response_model=dict)
async def list_pool(
    current_user: TokenPayload = Depends(get_current_user),
    service: ResourceService = Depends(get_resource_service),
):
    """内置能力池（Agent 配置页添加知识库/本体/Skill 时的可选项）"""
    pool_ids = {"knowledge": ["kb1", "kb2", "kb3"], "ontology": ["on1", "on2"], "skill": ["sk1", "sk2", "sk3"]}
    return {
        "knowledge": pool_ids_to_items(pool_ids["knowledge"]),
        "ontology": pool_ids_to_items(pool_ids["ontology"]),
        "skill": pool_ids_to_items(pool_ids["skill"]),
    }


def pool_ids_to_items(ids):
    """内置池基础信息（与前端 mock/agents.ts 对齐）"""
    pool_map = {
        "kb1": ("业务知识库", "平台业务规则与流程文档"),
        "kb2": ("产品文档库", "产品功能说明与使用手册"),
        "kb3": ("法规政策库", "行业法规与政策文件汇编"),
        "on1": ("业务本体", "领域概念与关系的语义模型"),
        "on2": ("数据本体", "数据字段与指标语义定义"),
        "sk1": ("数据分析技能", "数据查询、聚合与可视化"),
        "sk2": ("文档问答技能", "基于知识库的多轮问答流程"),
        "sk3": ("报告生成技能", "自动生成结构化业务报告"),
    }
    return [
        {"id": rid, "name": pool_map[rid][0], "description": pool_map[rid][1]}
        for rid in ids
        if rid in pool_map
    ]


@router.post("", response_model=ResourceResponse)
async def create_resource(
    payload: ResourceCreate,
    current_user: TokenPayload = Depends(get_current_user),
    service: ResourceService = Depends(get_resource_service),
):
    """新建资源（前端 '新建XXX' 按钮）"""
    if payload.type not in RESOURCE_TYPES:
        raise HTTPException(status_code=400, detail=f"非法资源类型: {payload.type}")
    resource = await service.create_resource(user_id=current_user.user_id, payload=payload)
    return _serialize(resource)


@router.get("/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    service: ResourceService = Depends(get_resource_service),
):
    """获取单个资源"""
    resource = await service.get_resource(current_user.user_id, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return _serialize(resource)


@router.put("/{resource_id}", response_model=ResourceResponse)
async def update_resource(
    resource_id: str,
    payload: ResourceUpdate,
    current_user: TokenPayload = Depends(get_current_user),
    service: ResourceService = Depends(get_resource_service),
):
    """更新资源"""
    resource = await service.get_resource(current_user.user_id, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    resource = await service.update_resource(resource, payload)
    return _serialize(resource)


@router.delete("/{resource_id}")
async def delete_resource(
    resource_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    service: ResourceService = Depends(get_resource_service),
):
    """删除资源"""
    resource = await service.get_resource(current_user.user_id, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    await service.delete_resource(resource)
    return {"message": "Resource deleted"}