"""Tool executor：从工具注册表统一执行工具。

支持两种来源，方便逐步迁移：
  - 传入 ToolDef 列表（推荐，配合 @tool 装饰器）
  - 传入 name->callable 的 dict（兼容旧式直接函数注册）
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List

from app.tools.base import ToolRegistry, inventory


class ToolExecutor:
    """执行已注册工具，统一捕获异常并返回结构化结果。"""

    def __init__(self, registry: ToolRegistry | None = None):
        # 便捷 fallback：允许旧式 func dict 注册。
        self.legacy: Dict[str, Callable[..., Any]] = {}
        # 默认使用进程级全局注册表（内置工具 import 时已注入）。
        self.registry = registry or inventory.registry

    def register_tool(self, name: str, func: Callable[..., Any]) -> None:
        """旧式注册：直接给一个 callable（无 schema 声明）。"""
        self.legacy[name] = func

    def list_names(self) -> list[str]:
        """返回全部可用工具名（注册表 + legacy）。"""
        return sorted(set(self.registry.names()) | set(self.legacy.keys()))

    async def execute(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """执行一个工具。找不到则返回失败结果；异常被捕获转为失败结果。"""
        if self.registry.get(tool_name):
            try:
                result = await self.registry.get(tool_name).fn(**tool_args)
                return self._ok(result, tool_name)
            except Exception as e:
                return self._err(str(e), tool_name)
        if tool_name in self.legacy:
            try:
                result = await self.legacy[tool_name](**tool_args)
                return self._ok(result, tool_name)
            except Exception as e:
                return self._err(str(e), tool_name)
        return self._err(f"Tool '{tool_name}' not found", tool_name)

    @staticmethod
    def _ok(result: Any, tool_name: str) -> Dict[str, Any]:
        return {"success": True, "result": result, "tool": tool_name}

    @staticmethod
    def _err(error: str, tool_name: str) -> Dict[str, Any]:
        return {"success": False, "error": error, "tool": tool_name}