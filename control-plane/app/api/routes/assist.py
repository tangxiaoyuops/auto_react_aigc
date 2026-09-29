"""Skill AI 辅助：生成/改写 Skill 文件（转发到认知层）。
"""
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx

from app.core.config import settings
from app.core.security import get_current_user, TokenPayload
from fastapi import Depends

router = APIRouter()
MODEL_PREFIX = "/api/v1/skill/assist"


class SkillAssistRequest(BaseModel):
    action: str = "generate"              # generate | rewrite
    description: str = ""
    current_files: Optional[Dict[str, str]] = None
    target: str = "all"
    name_hint: str = "custom-skill"
    model: Optional[str] = None


@router.post("/skill/assist")
async def skill_assist_forward(
    req: SkillAssistRequest,
    current_user: TokenPayload = Depends(get_current_user),
):
    """把 Skill 生成/改写请求转发到认知层。"""
    base = (settings.COGNITION_URL or "http://localhost:8000").rstrip("/")
    url = f"{base}{MODEL_PREFIX}"
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json=req.model_dump())
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"无法连接认知层: {e}")
    if resp.status_code != 200:
        detail = resp.text[:200]
        raise HTTPException(status_code=resp.status_code, detail=f"AI 辅助失败: {detail}")
    return resp.json()