"""skills 包：导入即触发内置 skill 注册到全局 skill_inventory。"""
from app.skills import builtin  # noqa: F401

__all__ = ["builtin", "base", "loader"]