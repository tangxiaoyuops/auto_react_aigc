"""RunSpec：配置态（Agent+资源引用）编译为运行时可执行契约。

配置态存的是资源 ID 引用；运行前由 control-plane 的 compile_runspec
解析为可执行数据，下发给 cognition-plane 按 RunSpec 运行。
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RunSpecKnowledge(BaseModel):
    """知识库检索配置"""
    resource_id: str
    name: str = ""
    top_k: int = 5


class RunSpec(BaseModel):
    """一次 Agent 运行的完整契约"""
    agent_id: str
    name: str = ""
    model: str = "gpt-4o"
    # 装配后的 system prompt（已含 prompt 资源模板 + skill 提示词）
    system_prompt: str = ""
    # 显式工具名（Agent.tool_ids）
    tools: List[str] = Field(default_factory=list)
    # skill 资源 ID（cognition 侧按 ID 装载）
    skills: List[str] = Field(default_factory=list)
    # 知识库资源（供检索增强，演示结构）
    knowledge: List[RunSpecKnowledge] = Field(default_factory=list)
    # 模型运行参数
    temperature: float = 0.7
    max_iterations: int = 10
    timeout: int = 300