"""Skill 装载器：把 RunSpec 中的 skill_ids 解析为可执行的提示词段 + 工具集。

核心职责（装配器的一环）：
  1. 优先从全局 skill_inventory（内置注册表）按 id/name 取出 SkillDef。
  2. 未命中的 id 视为"自定义 Skill 资源"，通过 control-plane 内部接口拉取
     文件树包（SKILL.md/references.md/fields.md/scripts/*.py），
     把 SKILL.md 渲染为提示词段。
  3. 为每个自定义 Skill 生成一个"专属脚本工具"（run_<skill>_script），
     skill_name 预绑定，避免 LLM 填错名字。
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.skills import base as _base  # noqa: F401 触发注册
from app.skills.base import SkillDef, skill_inventory
from app.core.config import settings
from app.tools.base import ToolDef


@dataclass
class SkillBundle:
    """一组 skill 的装配结果。"""

    skill_ids: List[str]
    prompt_sections: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    skill_defs: List[SkillDef] = field(default_factory=list)
    tool_defs: List[ToolDef] = field(default_factory=list)

    def render_system_prompt(self) -> str:
        """把所有 skill 提示词拼成一段独立 system prompt 追加内容。"""
        if not self.prompt_sections:
            return ""
        header = "\n\n## 能力说明（Skill）\n"
        body = "\n\n".join(section for section in self.prompt_sections if section.strip())
        return header + body


def _internal_key() -> str:
    """与 control-plane 保持一致的服务间密钥（派生自 SECRET_KEY + 固定盐）。"""
    return hashlib.sha256((settings.SECRET_KEY + ":skill-package").encode()).hexdigest()[:32]


def _render_skill_prompt(skill_id: str, pkg: Dict[str, Any], variables: Optional[Dict[str, Any]]) -> str:
    """把 SKILL.md 渲染为注入 system prompt 的提示词段。"""
    files = pkg.get("files") or {}
    md = files.get("SKILL.md", "")
    name = pkg.get("name") or skill_id
    description = pkg.get("description") or ""
    sections = []
    if description:
        sections.append(f"描述：{description}")
    if md.strip():
        sections.append(md.strip())
    else:
        sections.append("（该 Skill 未编写 SKILL.md 说明）")
    body = "\n".join(sections)
    if variables:
        try:
            body = body.format(**variables)
        except Exception:
            pass
    return body


def _script_names(pkg: Dict[str, Any]) -> List[str]:
    """返回该 Skill 文件树中 scripts/ 下的 .py 文件名（不含目录前缀）。"""
    files = pkg.get("files") or {}
    out = []
    for k in files:
        if k.startswith("scripts/") and k.endswith(".py"):
            rel = k[len("scripts/"):]
            if "/" not in rel and rel not in (".", ".."):
                out.append(rel)
    return out


def _safe_token(name: str) -> str:
    """把 skill 名转换为安全的工具名片段。"""
    return re.sub(r"[^a-zA-Z0-9_]", "_", name or "skill")


def _make_skill_tool(skill_name: str, scripts: List[str]) -> ToolDef:
    """为自定义 Skill 生成专属脚本执行工具（skill_name 预绑定）。"""
    from app.tools.base import inventory as _tool_inventory
    from app.tools.builtin.run_skill_script import execute as _exec_tooldef

    # 取底层可调用函数（ToolDef.fn）
    if hasattr(_exec_tooldef, "fn") and callable(_exec_tooldef.fn):
        _exec_impl = _exec_tooldef.fn
    else:
        _exec_impl = _exec_tooldef
    if not callable(_exec_impl):
        registered = _tool_inventory.get("run_skill_script")
        if registered and callable(registered.fn):
            _exec_impl = registered.fn

    token = _safe_token(skill_name)
    script_desc = "、".join(f"`{s}`" for s in scripts) if scripts else "（暂无脚本）"
    description = (
        f"执行 Skill「{skill_name}」携带的 Python 脚本（{script_desc}）并返回执行结果。"
        f"请选择其中一个脚本名，可传参数。"
    )

    async def fn(script: str, args: Optional[List[str]] = None) -> Dict[str, Any]:
        return await _exec_impl(skill_name=skill_name, script=script, args=args or [])

    return ToolDef(
        name=f"run_{token}_script",
        description=description,
        parameters={
            "script": {
                "type": "string",
                "required": True,
                "description": f"要执行的脚本文件名，可选：{script_desc}",
            },
            "args": {
                "type": "array",
                "items": {"type": "string"},
                "description": "传递给脚本的命令行参数（字符串数组，可选）",
            },
        },
        output="脚本执行的 dict（stdout/stderr/returncode）",
        fn=fn,
    )


def _http_get_json(url: str) -> Optional[Dict[str, Any]]:
    import urllib.request
    with urllib.request.urlopen(url, timeout=8) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _fetch_skill_package(skill_id: str) -> Optional[Dict[str, Any]]:
    """同步拉取 control-plane 的 Skill 文件树包（内部密钥）。失败返回 None。"""
    try:
        base = (settings.CONTROL_PLANE_URL or "http://localhost:8080").rstrip("/")
        url = f"{base}/api/v1/resources/skills/{skill_id}/package?internal_key={_internal_key()}"
        return _http_get_json(url)
    except Exception:
        return None


async def _fetch_skill_package_async(skill_id: str) -> Optional[Dict[str, Any]]:
    """异步拉取 control-plane 的 Skill 包（供 async 装配路径使用）。"""
    try:
        from concurrent.futures import ThreadPoolExecutor

        base = (settings.CONTROL_PLANE_URL or "http://localhost:8080").rstrip("/")
        url = f"{base}/api/v1/resources/skills/{skill_id}/package?internal_key={_internal_key()}"
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=1) as pool:
            return await loop.run_in_executor(pool, lambda: _http_get_json(url))
    except Exception as e:
        import logging
        logging.getLogger("skills.loader").warning(
            "fetch skill package failed: skill=%s base=%s err=%s",
            skill_id, settings.CONTROL_PLANE_URL, e,
        )
        return None


def _external_skill_tools_async(pkgs: List[Any]) -> List[ToolDef]:
    """由拉取到的包生成专属脚本工具。"""
    tools: List[ToolDef] = []
    for pkg in pkgs:
        if not isinstance(pkg, dict) or not pkg:
            continue
        name = pkg.get("name") or pkg.get("id") or ""
        if not name:
            continue
        tools.append(_make_skill_tool(name, _script_names(pkg)))
    return tools


def _build_bundle(skill_ids: List[str], all_defs: List[SkillDef], variables: Optional[Dict[str, Any]]) -> SkillBundle:
    """由 SkillDef 列表构建 SkillBundle（提示词段 + 工具收集）。"""
    bundle = SkillBundle(
        skill_ids=[sk.name for sk in all_defs],
        skill_defs=all_defs,
    )
    bundle.prompt_sections = [
        f"### Skill: {sk.name}\n{sk.render_prompt(variables)}"
        for sk in all_defs
    ]
    bundle.tools = []
    for sk in all_defs:
        for t in sk.tools:
            if t not in bundle.tools:
                bundle.tools.append(t)
    return bundle


def load_skills(skill_ids: List[str], variables: Optional[Dict[str, Any]] = None) -> SkillBundle:
    """按 skill_ids 装载 skill（内置 + 自定义资源），返回装配结果。"""
    if not skill_ids:
        return SkillBundle(skill_ids=[])

    local_defs = skill_inventory.get_by_ids(skill_ids)
    local_found = {sk.name for sk in local_defs}

    pkgs: List[Dict[str, Any]] = []
    external_defs: List[SkillDef] = []
    for sid in skill_ids:
        if sid in local_found:
            continue
        pkg = _fetch_skill_package(sid)
        if pkg:
            pkgs.append(pkg)
            name = pkg.get("name") or sid
            external_defs.append(SkillDef(
                name=name,
                description=pkg.get("description") or "",
                prompt_template=_render_skill_prompt(sid, pkg, None),
                tools=["run_skill_script"],
            ))

    all_defs = local_defs + external_defs
    bundle = _build_bundle(skill_ids, all_defs, variables)
    for t in _external_skill_tools_from_pkgs(pkgs):
        bundle.tool_defs.append(t)
    return bundle


async def load_skills_async(skill_ids: List[str], variables: Optional[Dict[str, Any]] = None) -> SkillBundle:
    """异步装载（供异步装配路径使用）。"""
    if not skill_ids:
        return SkillBundle(skill_ids=[])

    local_defs = skill_inventory.get_by_ids(skill_ids)
    local_found = {sk.name for sk in local_defs}

    tasks = [_fetch_skill_package_async(sid) for sid in skill_ids if sid not in local_found]
    pkgs = await asyncio.gather(*tasks, return_exceptions=True)
    pkgs = [p for p in pkgs if isinstance(p, dict) and p]

    external_defs: List[SkillDef] = []
    for pkg in pkgs:
        sid = pkg.get("id") or pkg.get("name") or ""
        if not sid:
            continue
        name = pkg.get("name") or sid
        external_defs.append(SkillDef(
            name=name,
            description=pkg.get("description") or "",
            prompt_template=_render_skill_prompt(sid, pkg, None),
            tools=["run_skill_script"],
        ))

    all_defs = local_defs + external_defs
    bundle = _build_bundle(skill_ids, all_defs, variables)
    for t in _external_skill_tools_from_pkgs(pkgs):
        bundle.tool_defs.append(t)
    return bundle


def _external_skill_tools_from_pkgs(pkgs: List[Dict[str, Any]]) -> List[ToolDef]:
    """由拉取到的包生成专属脚本工具。"""
    tools: List[ToolDef] = []
    for pkg in pkgs:
        name = pkg.get("name") or pkg.get("id") or ""
        if not name:
            continue
        tools.append(_make_skill_tool(name, _script_names(pkg)))
    return tools