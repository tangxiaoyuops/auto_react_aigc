"""内置 Skill 示例，注册到全局 skill_inventory。

Skill 名称与前端资源池（mock/agents.ts + 后端 resources/_builtin_pool）对齐，
便于 Agent 挂载后运行时能匹配到。
使用 @skill 装饰器声明；exec_fn 为可选自定义逻辑，仅演示结构。
"""
from app.skills.base import skill, skill_inventory


@skill(
    name="sk1",
    description="数据分析技能：数据查询、聚合与可视化",
    prompt_template=(
        "你具备经营数据分析能力。当处理数据类任务时：\n"
        "- 先明确指标口径与对比周期（如环比/同比）。\n"
        "- 优先调用可用的计算与分析工具量化结果，再做归因。\n"
        "- 输出结构化结论，并给出可执行建议。"
    ),
    tools=["calculator"],
)
async def sales_analysis() -> dict:
    """示例：数据分析技能的执行逻辑（业务内置可覆盖）。"""
    return {"status": "ok", "skill": "sales_analysis"}


@skill(
    name="sk2",
    description="文档问答技能：基于知识库的多轮问答流程",
    prompt_template=(
        "你具备知识库问答能力。回答问题时：\n"
        "- 优先检索并引用知识库相关内容作为依据。\n"
        "- 信息不足时明确说明，避免臆测。"
    ),
    tools=[],
)
async def doc_qa() -> dict:
    """示例：文档问答技能执行逻辑。"""
    return {"status": "ok", "skill": "doc_qa"}


@skill(
    name="sk3",
    description="报告生成技能：自动生成结构化业务报告",
    prompt_template=(
        "你具备报告生成能力。输出报告时应：\n"
        "- 结构化（标题/分节/要点）。\n"
        "- 结论先行，数据支撑，附下一步建议。"
    ),
    tools=[],
)
async def report_gen() -> dict:
    """示例：报告生成技能执行逻辑。"""
    return {"status": "ok", "skill": "report_gen"}


# 注册到进程级 skill 注册表
skill_inventory.register(sales_analysis)
skill_inventory.register(doc_qa)
skill_inventory.register(report_gen)