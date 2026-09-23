"""LLM Gateway for multi-model support"""
from typing import Optional, List
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel

from app.core.config import settings


class LLMGateway:
    """LLM Gateway for managing multiple LLM providers"""
    
    def __init__(self, model: str = None, temperature: float = 0.7):
        self.model = model or settings.DEFAULT_MODEL
        self.temperature = temperature
        self.llm = self._create_llm()
    
    def _create_llm(self) -> BaseChatModel:
        """Create LLM instance based on model name
        
        接入 AIMP Qwen3-5-397B NoThink (OpenAI 兼容，禁用思考) 作为主要真实模型。
        - 配置了 AIMP key 时，所有 OpenAI 兼容请求统一走 AIMP Qwen；
        - 仅当显式请求 claude 且配置了 Anthropic key 才用 claude。
        """
        if self.model.startswith("claude") and settings.ANTHROPIC_API_KEY:
            return ChatAnthropic(
                model=self.model,
                temperature=self.temperature,
                anthropic_api_key=settings.ANTHROPIC_API_KEY
            )
        if settings.AIMP_OPENAI_API_KEY:
            # AIMP Qwen3-5-397B NoThink (OpenAI 兼容接口)，禁用思考模式
            return ChatOpenAI(
                model=settings.QWEN3_5_MODEL,
                temperature=self.temperature,
                openai_api_key=settings.AIMP_OPENAI_API_KEY,
                openai_api_base=settings.AIMP_OPENAI_API_BASE,
                extra_body={
                    "chat_template_kwargs": {"enable_thinking": settings.QWEN3_5_ENABLE_THINKING}
                },
            )
        if self.model.startswith("gpt") and settings.OPENAI_API_KEY:
            return ChatOpenAI(
                model=self.model,
                temperature=self.temperature,
                openai_api_key=settings.OPENAI_API_KEY
            )
        # 无有效 key 时兜底，仍走 OpenAI（运行时将报认证错误，外层会转 Mock）
        return ChatOpenAI(
            model="gpt-4o",
            temperature=self.temperature,
            openai_api_key=settings.OPENAI_API_KEY
        )
    
    async def ainvoke(self, messages: List[BaseMessage]) -> BaseMessage:
        """Invoke LLM asynchronously"""
        return await self.llm.ainvoke(messages)
    
    async def astream(self, messages: List[BaseMessage]):
        """Stream LLM response"""
        async for chunk in self.llm.astream(messages):
            yield chunk
    
    def bind_tools(self, tools: List[dict]):
        """Bind tools to LLM"""
        return self.llm.bind_tools(tools)
