"""Skill 装载器：把 RunSpec 中的 skill_ids 解析为可执行的提示词段 + 工具集。

核心职责（装配器的一环）：
  1. 按 skill_ids 从全局 skill_inventory 取出 SkillDef。
  2. 把每个 skill 的 prompt_template 拼接为一段可注入 system prompt 的内容。
  3. 收集 skill 携带的工具名，供 engine 过滤工具 schema。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from app.skills import base as _base  # noqa: F401 触发注册
from app.skills.base import SkillDef, skill_inventory


@dataclass
class SkillBundle:
    """一组 skill 的装配结果。"""

    skill_ids: List[str]
    prompt_sections: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    skill_defs: List[SkillDef] = field(default_factory=list)

    def render_system_prompt(self) -> str:
        """把所有 skill 提示词拼成一段独立 system prompt 追加内容。"""
        if not self.prompt_sections:
            return ""
        header = "\n\n## 能力说明（Skill）\n"
        body = "\n\n".join(section for section in self.prompt_sections if section.strip())
        return header + body


def load_skills(skill_ids: List[str], variables: Dict[str, Any] | None = None) -> SkillBundle:
    """按 skill_ids 装载 skill，返回装配结果。不存在 id 会静默跳过（不报错）。"""
    if not skill_ids:
        return SkillBundle(skill_ids=[])
    skill_defs = skill_inventory.get_by_ids(skill_ids)
    bundle = SkillBundle(
        skill_ids=[sk.name for sk in skill_defs],
        skill_defs=skill_defs,
    )
    bundle.prompt_sections = [
        f"### Skill: {sk.name}\n{sk.render_prompt(variables)}"
        for sk in skill_defs
    ]
    bundle.tools = skill_inventory.collect_tools(skill_ids)
    return bundle