"""Skill 生成/改写接口（认知层）。

供控制平面转发调用：POST /api/v1/skill/assist
请求：{ action, description, current_files?, target?, name_hint?, model? }
响应：{ files: {path: content} }
"""
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.skill_gen_service import assist_skill

router = APIRouter()


class SkillAssistRequest(BaseModel):
    action: str = "generate"          # generate | rewrite
    description: str = ""
    current_files: Optional[Dict[str, str]] = None
    target: str = "all"
    name_hint: str = "custom-skill"
    model: Optional[str] = None


class SkillAssistResponse(BaseModel):
    files: Dict[str, str]
    raw: Optional[str] = None


@router.post("/assist", response_model=SkillAssistResponse)
async def skill_assist(req: SkillAssistRequest):
    """生成或改写 Skill 文件树内容。"""
    if req.action not in ("generate", "rewrite"):
        raise HTTPException(status_code=400, detail=f"action 必须为 generate/rewrite，收到: {req.action}")
    try:
        result = await assist_skill(
            action=req.action,
            description=req.description,
            current_files=req.current_files,
            target=req.target,
            name_hint=req.name_hint,
            model=req.model,
        )
    except Exception as e:  # LLM 网络/鉴权失败
        raise HTTPException(status_code=502, detail=f"AI 生成失败: {e}")
    if not result.get("files"):
        raise HTTPException(
            status_code=502,
            detail=f"AI 未返回有效文件：{result.get('raw', '')[:200]}",
        )
    return SkillAssistResponse(files=result["files"], raw=result.get("raw"))