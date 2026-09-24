"""tools 包：导入即触发内置工具注册到全局 inventory。"""
from app.tools import builtin  # noqa: F401

__all__ = ["builtin", "base", "executor"]