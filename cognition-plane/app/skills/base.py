"""Skill 运行时定义与注册表（Cordis 风格轻量插件化）。

一个 Skill = 一段可注入的提示词模板 + 可挂载的工具 + 可选执行函数。
Skill 通过 @skill 装饰器声明，注册到进程级 skill_inventory，
Agent 运行前由 loader 按 skill_ids 动态装载，把 prompt 并入 system prompt，
并把 skill 携带的工具并入工具集。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional


# Skill 执行函数签名（可选，用于自定义技能逻辑）
SkillFn = Callable[..., Awaitable[Dict[str, Any]]]


@dataclass
class SkillDef:
    """一个 Skill 的定义。"""

    name: str
    description: str
    prompt_template: str                 # 注入 system prompt 的提示词片段（可含 {var} 占位）
    tools: List[str] = field(default_factory=list)   # 本 skill 挂载的工具名
    exec_fn: Optional[SkillFn] = None    # 可选自定义执行逻辑

    def render_prompt(self, variables: Optional[Dict[str, Any]] = None) -> str:
        """渲染 skill 提示词；key 不存在时保留原占位，避免崩溃。"""
        if not variables:
            return self.prompt_template
        return self.prompt_template.format(**variables)


class SkillRegistry:
    """Skill 注册表：name -> SkillDef，同名覆盖（便于热替换）。"""

    def __init__(self) -> None:
        self._skills: Dict[str, SkillDef] = {}

    def register(self, skill_def: SkillDef) -> None:
        self._skills[skill_def.name] = skill_def

    def get(self, name: str) -> Optional[SkillDef]:
        return self._skills.get(name)

    def names(self) -> List[str]:
        return list(self._skills.keys())

    def get_by_ids(self, ids: List[str]) -> List[SkillDef]:
        """按 skill 资源 ID/名称批量取（按传入顺序）。"""
        result = []
        for sid in ids:
            sk = self._skills.get(sid)
            if sk:
                result.append(sk)
        return result

    def collect_tools(self, ids: List[str]) -> List[str]:
        """收集一组 skill 挂载的全部工具名（去重保序）。"""
        seen: set = set()
        out: List[str] = []
        for sk in self.get_by_ids(ids):
            for tool_name in sk.tools:
                if tool_name not in seen:
                    seen.add(tool_name)
                    out.append(tool_name)
        return out


class SkillInventory:
    """进程级 Skill 默认注册表（模拟 Cordis 单例 ctx.skills）。"""

    def __init__(self) -> None:
        self.registry: SkillRegistry = SkillRegistry()

    def register(self, skill_def: SkillDef) -> None:
        self.registry.register(skill_def)

    def get(self, name: str) -> Optional[SkillDef]:
        return self.registry.get(name)

    def names(self) -> List[str]:
        return self.registry.names()

    def get_by_ids(self, ids: List[str]) -> List[SkillDef]:
        return self.registry.get_by_ids(ids)

    def collect_tools(self, ids: List[str]) -> List[str]:
        return self.registry.collect_tools(ids)


def skill(
    name: str,
    description: str,
    prompt_template: str,
    tools: Optional[List[str]] = None,
) -> Callable[[SkillFn], SkillDef]:
    """装饰器：把一个函数声明为一个 Skill。"""
    def decorator(fn: SkillFn) -> SkillDef:
        return SkillDef(
            name=name,
            description=description,
            prompt_template=prompt_template,
            tools=tools or [],
            exec_fn=fn,
        )
    return decorator


# 进程级默认单例：skills/builtin import 时注入
skill_inventory: SkillInventory = SkillInventory()