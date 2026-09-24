"""Cordis 风格的轻量工具插件化层。

目标：让工具像 Cordis 一样「自描述、自注册、自动生成 schema」，
消除 engine.py 中手写 `_build_tool_schemas()` 导致的重复与散乱。

用法：
    from app.tools.base import tool, inventory

    @tool(
        name="calculator",
        description="安全计算数学表达式",
        parameters={
            "expression": {"type": "string", "required": True, "description": "要计算的表达式"},
        },
        output="计算结果的 dict",
    )
    async def calculator(expression: str) -> dict:
        return {"expression": expression, "result": 42}

    然后 registry.schemas() 自动产出 OpenAI function-calling schema，
    工具调用可统一走 ToolExecutor，实现"一处定义、处处可用"。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional


# 工具执行函数签名：接收关键字参数，返回 dict
ToolFn = Callable[..., Awaitable[Dict[str, Any]]]


@dataclass
class ToolDef:
    """一个工具的定义。schema 与 execute 合并在同一对象中。"""

    name: str
    description: str
    parameters: Dict[str, Any]
    output: Optional[str]
    fn: ToolFn

    def to_schema(self) -> Dict[str, Any]:
        """转换为 OpenAI function-calling schema。

        由 this.parameters（{name: {type, required, description, enum?}}）
        自动生成 properties 与 required 列表。
        """
        properties: Dict[str, Any] = {}
        required: List[str] = []
        for pname, p in self.parameters.items():
            prop: Dict[str, Any] = {"type": p.get("type", "string"), "description": p.get("description", "")}
            if "enum" in p:
                prop["enum"] = p["enum"]
            properties[pname] = prop
            if p.get("required", False):
                required.append(pname)
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {"type": "object", "properties": properties, "required": required},
            },
        }


class ToolRegistry:
    """工具注册表：注册即获得 schema，类型与 Cordis 的 ctx.tools 对齐。"""

    __slots__ = ("_tools",)

    def __init__(self) -> None:
        self._tools: Dict[str, ToolDef] = {}

    def register(self, tool_def: ToolDef) -> None:
        """注册一个工具；同名重复注册会覆盖（便于热替换）。"""
        self._tools[tool_def.name] = tool_def

    def get(self, name: str) -> Optional[ToolDef]:
        """按名字取工具；未注册返回 None。"""
        return self._tools.get(name)

    def names(self) -> List[str]:
        """返回全部已注册工具名。"""
        return list(self._tools.keys())

    def schemas(self) -> List[Dict[str, Any]]:
        """返回全部工具的 OpenAI function-calling schema（供模型绑定）。"""
        return [t.to_schema() for t in self._tools.values()]


def tool(name: str, description: str, parameters: Dict[str, Any], output: Optional[str] = None) -> Callable[[ToolFn], ToolDef]:
    """装饰器：把一个异步函数声明为一个工具。"""
    def decorator(fn: ToolFn) -> ToolDef:
        return ToolDef(name=name, description=description, parameters=parameters, output=output, fn=fn)
    return decorator


class ToolInventory:
    """进程级默认注册表，模拟 Cordis 的单例 ctx.tools。"""

    __slots__ = ("registry",)

    def __init__(self) -> None:
        self.registry: ToolRegistry = ToolRegistry()

    def register(self, tool_def: ToolDef) -> None:
        self.registry.register(tool_def)

    def get(self, name: str) -> Optional[ToolDef]:
        return self.registry.get(name)

    def names(self) -> List[str]:
        return self.registry.names()

    def schemas(self) -> List[Dict[str, Any]]:
        return self.registry.schemas()


# 进程级默认单例：tools/inventory.register(...)，modules import 时自动带货
inventory: ToolInventory = ToolInventory()