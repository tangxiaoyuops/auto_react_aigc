"""LangGraph Agent Engine"""
from typing import TypedDict, Annotated, Sequence
import operator
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import asyncio

from app.llm.gateway import LLMGateway
from app.tools.executor import ToolExecutor
from app.core.config import settings


class AgentState(TypedDict):
    """Agent state"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    thoughts: Annotated[Sequence[str], operator.add]
    tool_calls: Annotated[Sequence[dict], operator.add]
    observations: Annotated[Sequence[str], operator.add]
    current_thought: str
    next_action: str
    iteration: int
    max_iterations: int
    final_answer: str


class AgentEngine:
    """LangGraph-based Agent Engine"""
    
    def __init__(
        self,
        model: str = None,
        tools: list = None,
        event_emitter=None
    ):
        self.model = model or settings.DEFAULT_MODEL
        self.tools = tools or []
        self.event_emitter = event_emitter
        self.llm_gateway = LLMGateway(model=self.model)
        self.tool_executor = ToolExecutor()
        self.checkpointer = MemorySaver()
        
        # Build workflow graph
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("reasoning", self._reasoning_node)
        workflow.add_node("tool_executor", self._tool_executor_node)
        
        # Set entry point
        workflow.set_entry_point("reasoning")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "reasoning",
            self._should_continue,
            {
                "continue": "tool_executor",
                "end": END
            }
        )
        
        workflow.add_edge("tool_executor", "reasoning")
        
        # Compile
        return workflow.compile(checkpointer=self.checkpointer)
    
    async def _reasoning_node(self, state: AgentState):
        """Reasoning node"""
        # Emit thought event
        if self.event_emitter:
            await self.event_emitter.emit("REASONING_START", {
                "step": state["iteration"]
            })
        
        # Call LLM
        response = await self.llm_gateway.ainvoke(state["messages"])
        
        # Emit reasoning content
        if self.event_emitter:
            await self.event_emitter.emit("REASONING_CONTENT", {
                "content": response.content,
                "node_name": "思考",
            })
            await self.event_emitter.emit("REASONING_END", {})
        
        # Check for tool calls
        if hasattr(response, "tool_calls") and response.tool_calls:
            return {
                "tool_calls": response.tool_calls,
                "next_action": "tool",
                "current_thought": response.content
            }
        else:
            # Final answer
            if self.event_emitter:
                await self.event_emitter.emit("TEXT_MESSAGE_START", {})
                await self.event_emitter.emit("TEXT_MESSAGE_CONTENT", {
                    "content": response.content
                })
                await self.event_emitter.emit("TEXT_MESSAGE_END", {})
            
            return {
                "messages": [response],
                "final_answer": response.content,
                "next_action": "end"
            }
    
    async def _tool_executor_node(self, state: AgentState):
        """Tool executor node"""
        results = []
        
        for tool_call in state["tool_calls"]:
            tool_name = tool_call.get("name", "")
            tool_args = tool_call.get("args", {})
            
            # Emit tool call start
            if self.event_emitter:
                await self.event_emitter.emit("TOOL_CALL_START", {
                    "tool_name": tool_name,
                    "tool_args": tool_args,
                    "node_name": tool_name,
                    "status": "running",
                })
            
            start_ts = asyncio.get_event_loop().time()
            
            # Execute tool
            result = await self.tool_executor.execute(tool_name, tool_args)
            
            duration_ms = int((asyncio.get_event_loop().time() - start_ts) * 1000)
            
            # Emit tool result
            if self.event_emitter:
                await self.event_emitter.emit("TOOL_RESULT", {
                    "tool_name": tool_name,
                    "result": result,
                    "node_name": tool_name,
                    "status": "success" if result.get("success") else "failed",
                    "duration_ms": duration_ms,
                })
            
            results.append(result)
        
        # Create observation
        observation = "\n".join([
            f"Tool: {r.get('tool')}\nResult: {r.get('result', r.get('error'))}"
            for r in results
        ])
        
        if self.event_emitter:
            await self.event_emitter.emit("OBSERVATION", {
                "content": observation,
                "result": observation,
            })
        
        return {
            "observations": [observation],
            "iteration": state["iteration"] + 1,
            "next_action": "reasoning"
        }
    
    def _should_continue(self, state: AgentState):
        """Determine if should continue"""
        if state["next_action"] == "end":
            return "end"
        
        if state["iteration"] >= state["max_iterations"]:
            return "end"
        
        return "continue"
    
    async def run(
        self,
        message: str,
        system_prompt: str = None,
        thread_id: str = None
    ):
        """Execute agent"""
        # 兜底 mock 模式：无 LLM API Key 时输出模拟 Trace，保证链路可跑通
        if settings.MOCK_MODE:
            return await self._run_mock(message)

        # Build initial messages
        messages = []
        
        if system_prompt:
            from langchain_core.messages import SystemMessage
            messages.append(SystemMessage(content=system_prompt))
        
        messages.append(HumanMessage(content=message))
        
        # Initial state
        initial_state = {
            "messages": messages,
            "thoughts": [],
            "tool_calls": [],
            "observations": [],
            "current_thought": "",
            "next_action": "",
            "iteration": 0,
            "max_iterations": settings.MAX_ITERATIONS,
            "final_answer": ""
        }
        
        # Run graph
        config = {"configurable": {"thread_id": thread_id or "default"}}
        
        final_state = await self.graph.ainvoke(initial_state, config)
        
        return final_state["final_answer"]

    async def _run_mock(self, message: str) -> str:
        """Mock 模式：仿真一段多轮「自主规划」执行轨迹（无 API Key 时使用）

        相比固定模板，这里会输出：任务理解 -> 方案规划 -> 多轮(推理->工具->反思) -> 汇总报告，
        让前端看到的不再是"平的 mock"，而是一段有递进、有分支判断的规划过程。
        """
        lower = message.lower()

        # 0) 任务理解 + 方案规划（拆解子步骤）
        plan = self._mock_plan(lower)
        await self._emit_note("任务理解", f"解析用户意图「{message}」，识别目标为：{plan['goal']}")
        await self._emit_note("方案规划", plan["overview"])
        await self._emit_note(
            "方案拆解",
            "我计划按以下步骤推进：\n" + plan["steps"],
        )

        # 1) 逐轮执行：推理 -> 工具 -> 反思
        for i, tool in enumerate(plan["tools"]):
            reason = tool["reason"]
            await self._emit_note(f"第 {i + 1} 步 · 推理", reason)
            await self._mock_tool(tool["name"], tool["args"], tool["result"])
            # 反思：基于工具结果判断下一步
            if tool["reason_after"]:
                await self._emit_note(f"第 {i + 1} 步 · 反思", tool["reason_after"])

        # 2) 生成结构化报告
        report = plan["report"]
        if self.event_emitter:
            await self.event_emitter.emit("REASONING_CONTENT", {
                "content": "所有子任务已完成，我把各步结论汇总为结构化报告，并补充下一步建议。",
                "node_name": "结论汇总",
            })
            await self.event_emitter.emit("TEXT_MESSAGE_CONTENT", {"content": report})
        return report

    # ---- mock 规划与推理辅助 ----
    async def _emit_note(self, node_name: str, content: str) -> None:
        """发送一条思考/规划类事件"""
        if self.event_emitter:
            await self.event_emitter.emit("REASONING_CONTENT", {
                "content": content,
                "node_name": node_name,
            })

    def _mock_plan(self, lower: str) -> dict:
        """根据用户输入生成一套仿真「规划-执行-分析」蓝图（返回结构化的 mock 数据）

        返回: dict with keys: goal, overview, steps, tools[], report
        """
        if any(k in lower for k in ("销售", "数据", "分析", "钱", "预算", "成本", "环比", "报表")):
            return self._sales_plan()
        return self._generic_plan()

    def _sales_plan(self) -> dict:
        """销售数据分析场景：多轮规划 + 递进推理，体现自主规划感"""
        tools = [
            {
                "name": "query_sales",
                "args": {"range": "近三个月", "granularity": "按周"},
                "result": "返回 1,286 条销售记录\n时间跨度：近 90 天，覆盖 12 个区域 / 3 条产品线\n总销售额约 ￥4.2M",
                "reason": "首先获取近三个月的销售明细，按周聚合，才能观察到趋势与异常点。",
                "reason_after": "数据总览到手：总量 ￥4.2M。我注意到环比需要与前三个月做对比，因此继续计算环比指标。",
            },
            {
                "name": "compute_metrics",
                "args": {"metric": ["环比", "同比", "复购"], "compare": "上一周期"},
                "result": "环比 +12.4%｜同比 +18.1%｜复购率 34%\n高价值客户贡献占比升至 42%（上月 30%）",
                "reason": "已有明细，现计算核心指标：环比、同比、复购率，并定位驱动因子。",
                "reason_after": "环比 +12.4% 主要由高价值客户贡献率上升（30%→42%）驱动，而非全量增长，需进一步细分客群确认。",
            },
            {
                "name": "segment_analysis",
                "args": {"dimension": "客户价值分层", "by": ["高价值", "中价值", "流失"]},
                "result": "高价值客群增长 +25%（贡献 42%）\n流失客群环比 -8%，多为静默 60 天以上用户",
                "reason": "驱动因子指向客群分层，细分高/中/流失三层，定位增长与风险来源。",
                "reason_after": "结论明确：增长主要来自高价值客群，其余层级持平，需关注流失客群唤醒。",
            },
        ]
        return {
            "goal": "近三个月销售表现分析 + 环比解读 + 下一步建议",
            "overview": (
                "该目标属于「经营分析」类型，涉及多步骤：取数 → 算指标 → 分客群 → 下结论。\n"
                "我选择用「数据驱动」范式：先量化，再归因，最后给行动建议。"
            ),
            "steps": (
                "1. 拉取近三个月销售明细并按周聚合\n"
                "2. 计算环比/同比/复购等核心指标\n"
                "3. 按客户价值分层定位驱动因子\n"
                "4. 汇总结论并输出可执行建议"
            ),
            "tools": tools,
            "report": (
                "## 销售数据分析报告（Mock 仿真）\n\n"
                "**1. 总量与趋势**\n近 90 天销售额约 ￥4.2M，环比上月 **+12.4%**，同比 **+4.1%**。\n\n"
                "**2. 关键指标的归因**\n增长主要由高价值客群贡献率上升驱动（30% → 42%），属结构性改善而非季节性波动。\n\n"
                "**3. 风险点**\n中低价值客群环比持平，流失客群占比 -9%，主要集中为静默 60 天以上用户。\n\n"
                "**4. 下一步建议**\n- 加码高价值客群的个性化运营与复购激励\n"
                "- 对静默客群启动唤醒触达（短信/优惠券）\n"
                "- 每两周校验一次环比拆解，验证策略效果\n\n"
                "（以上为 Mock 模式仿真数据，接入真实 LLM 后将基于真实结果生成。）"
            ),
        }

    def _generic_plan(self) -> dict:
        """通用意图场景：规划 + 知识检索"""
        return {
            "goal": "理解通用业务问题并检索相关知识回答",
            "overview": (
                "该问题体量较小，采用「先检索后归纳」的策略：定位业务知识 → 提取关键点 → 组织回答。"
            ),
            "steps": "1. 语义检索相关业务知识\n2. 校验相关性并抽取要点\n3. 组织成结构化回答",
            "tools": [
                {
                    "name": "retrieve_kb",
                    "args": {"query": "业务知识检索", "top_k": 3},
                    "result": "命中 3 条相关业务文档（置信度 0.92 / 0.85 / 0.76）",
                    "reason": "先做语义检索，圈定与问题相关的知识片段。",
                    "reason_after": "已命中高相关片段，选取置信度最高的两条作为回答依据。",
                }
            ],
            "report": (
                "我基于业务知识库检索到了相关问题的高相关度内容（置信度 0.85+）。\n\n"
                "结合问题要点，我的回答整理如下：\n"
                "1. 该问题通常可从流程、责任与数据口径三个方面拆解；\n"
                "2. 优先参照已沉淀的标准流程执行，避免重复造轮子。\n\n"
                "如需更精确的数据口径，我可以进一步调用更多分析工具。（Mock 仿真）"
            ),
        }

    async def _mock_tool(self, tool_name: str, args: dict, result_text: str):
        """Mock 模式辅助：输出一次工具调用完整生命周期"""
        if not self.event_emitter:
            return
        await self.event_emitter.emit("TOOL_CALL_START", {
            "tool_name": tool_name,
            "tool_args": args,
            "node_name": tool_name,
        })
        await asyncio.sleep(0.4)
        await self.event_emitter.emit("TOOL_RESULT", {
            "tool_name": tool_name,
            "result": result_text,
            "node_name": tool_name,
            "duration_ms": 400 + (abs(hash(tool_name)) % 800),
        })
