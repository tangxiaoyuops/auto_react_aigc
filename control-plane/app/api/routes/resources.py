"""Resource 路由：5 类资源统一 CRUD + Skill 文件树读写"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.core.config import settings
from app.core.security import get_current_user, TokenPayload
from app.services.resource_service import ResourceService
from app.services.skill_file_service import SkillFileStore
from shared.schemas.resource import (
    RESOURCE_TYPES, ResourceCreate, ResourceUpdate, ResourceResponse,
)

router = APIRouter()


def get_resource_service(db: AsyncSession = Depends(get_db)) -> ResourceService:
    return ResourceService(db=db)


def get_skill_file_store(db: AsyncSession = Depends(get_db)) -> SkillFileStore:
    return SkillFileStore(db=db)


class SkillFilesUpdate(BaseModel):
    """整体覆盖 Skill 文件树"""
    files: Dict[str, str]


class SkillRunRequest(BaseModel):
    """运行 Skill 脚本请求"""
    script: str
    args: list = None


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
    """内置能力池（Agent 配置页添加知识库/本体/Skill 时的可选项）

    优先从库中按类型取池成员（origin='seed'），并附带未入库的内置缺省池，
    保证新旧前端都能拿到数据。
    """
    seeded = await service.list_resources(
        user_id=current_user.user_id, resource_type=None, keyword=None,
        page=1, page_size=500,
    )
    by_type: dict[str, list] = {"knowledge": [], "ontology": [], "skill": [], "tool": []}
    for r in seeded:
        if r.type == "kb":
            by_type["knowledge"].append({"id": r.id, "name": r.name, "description": r.description or ""})
        elif r.type == "ontology":
            by_type["ontology"].append({"id": r.id, "name": r.name, "description": r.description or ""})
        elif r.type == "skill":
            by_type["skill"].append({"id": r.id, "name": r.name, "description": r.description or ""})
        elif r.type == "tool":
            by_type["tool"].append({"id": r.id, "name": r.name, "description": r.description or ""})
    # 内置缺省池（离线/无数据兜底）
    builtin = _builtin_pool()
    for category, items in by_type.items():
        known = {i["id"] for i in items}
        for b in builtin.get(category, []):
            if b["id"] not in known:
                items.append(b)
    return by_type


def _builtin_pool():
    """内置缺省池（与前端 mock/agents.ts 对齐），新装无数据时兜底"""
    return {
        "knowledge": [
            {"id": "kb1", "name": "业务知识库", "description": "平台业务规则与流程文档"},
            {"id": "kb2", "name": "产品文档库", "description": "产品功能说明与使用手册"},
            {"id": "kb3", "name": "法规政策库", "description": "行业法规与政策文件汇编"},
        ],
        "ontology": [
            {"id": "on1", "name": "业务本体", "description": "领域概念与关系的语义模型"},
            {"id": "on2", "name": "数据本体", "description": "数据字段与指标语义定义"},
        ],
        "skill": [
            {"id": "sk1", "name": "数据分析技能", "description": "数据查询、聚合与可视化"},
            {"id": "sk2", "name": "文档问答技能", "description": "基于知识库的多轮问答流程"},
            {"id": "sk3", "name": "报告生成技能", "description": "自动生成结构化业务报告"},
        ],
        "tool": [
            {"id": "tool_calculator", "name": "Calculator", "description": "数学表达式精确计算"},
            {"id": "tool_web_search", "name": "Web Search", "description": "联网搜索信息"},
        ],
    }


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


# ---------- Skill 文件树（Cursor/Claude 风格 files） ----------

def _internal_key() -> str:
    """内部服务间访问密钥（认知层加载 Skill 包时使用，派生自 SECRET_KEY）。"""
    import hashlib
    return hashlib.sha256((settings.SECRET_KEY + ":skill-package").encode()).hexdigest()[:32]


@router.get("/skills/{resource_id}/package")
async def get_skill_package(
    resource_id: str,
    internal_key: str = None,
    store: SkillFileStore = Depends(get_skill_file_store),
):
    """内部接口：按 Skill 资源 ID 返回完整文件树包（供认知层 load_skills 拉取）。

    认证：使用派生自 SECRET_KEY 的 internal_key（query 参数），
    仅服务间内部调用，不暴露给浏览器前端。
    """
    if internal_key != _internal_key():
        raise HTTPException(status_code=403, detail="invalid internal key")
    resource = await store.get_resource_for_internal(resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Skill not found")
    if resource.type != "skill":
        raise HTTPException(status_code=400, detail="仅 Skill 资源支持文件树包")
    return {
        "id": resource.id,
        "name": resource.name,
        "description": resource.description,
        "files": store.get_files(resource),
    }


@router.get("/skills/{resource_id}/files")
async def list_skill_files(
    resource_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    store: SkillFileStore = Depends(get_skill_file_store),
):
    """返回 Skill 文件树（path -> content）。仅 skill 类型资源可用。"""
    resource = await store.get_resource(current_user.user_id, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    if resource.type != "skill":
        raise HTTPException(status_code=400, detail="仅 Skill 资源支持文件树")
    return {"resource_id": resource_id, "files": store.get_files(resource)}


@router.get("/skills/{resource_id}/files/{file_path:path}")
async def get_skill_file(
    resource_id: str,
    file_path: str,
    current_user: TokenPayload = Depends(get_current_user),
    store: SkillFileStore = Depends(get_skill_file_store),
):
    """读取单个 Skill 文件内容。"""
    resource = await store.get_resource(current_user.user_id, resource_id)
    if not resource or resource.type != "skill":
        raise HTTPException(status_code=404, detail="Resource not found")
    content = store.get_file_content(resource, file_path)
    if content is None:
        raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")
    return {"path": file_path, "content": content}


@router.put("/skills/{resource_id}/files")
async def update_skill_files(
    resource_id: str,
    payload: SkillFilesUpdate,
    current_user: TokenPayload = Depends(get_current_user),
    store: SkillFileStore = Depends(get_skill_file_store),
):
    """整体覆盖 Skill 文件树（并落盘 scripts/*.py 到磁盘工作区）。"""
    resource = await store.get_resource(current_user.user_id, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    if resource.type != "skill":
        raise HTTPException(status_code=400, detail="仅 Skill 资源支持文件树")
    # 校验路径，杜绝穿越
    for p in payload.files:
        if ".." in p.replace("\\", "/").split("/"):
            raise HTTPException(status_code=400, detail=f"非法路径: {p}")
    files = await store.write_files(resource, payload.files)
    return {"resource_id": resource_id, "files": files}


@router.post("/skills/{resource_id}/run")
async def run_skill_script_endpoint(
    resource_id: str,
    payload: SkillRunRequest,
    current_user: TokenPayload = Depends(get_current_user),
    store: SkillFileStore = Depends(get_skill_file_store),
):
    """编辑器「运行」：执行 Skill 的 Python 脚本（同步落盘后 subprocess 隔离执行）。

    与 Cognition 层 run_skill_script 工具共用同一套磁盘工作区与安全校验。
    """
    resource = await store.get_resource(current_user.user_id, resource_id)
    if not resource or resource.type != "skill":
        raise HTTPException(status_code=404, detail="Skill not found")
    # 确保脚本已落盘（编辑器可能在保存前直接运行）
    store._sync_scripts_to_disk(resource.id, resource.name, store.get_files(resource))
    from app.services.skill_file_service import run_skill_script_async
    return await run_skill_script_async(resource.name, payload.script, payload.args or [])


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