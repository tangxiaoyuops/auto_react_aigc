export interface Step {
  nodeType: string;
  nodeName: string;
  // 简短标题说明
  title: string;
  // 展开后的详细描述（TOOL 节点可能没有，用 input/result 呈现）
  detail?: string;
  // 工具相关（TOOL 节点）
  input?: string;
  result?: string;
  // 耗时（毫秒）
  duration?: number;
  status: 'running' | 'success' | 'error';
}

let msgId = 1000;

export function nextMsgId(): number {
  return msgId++;
}

// 模拟回复生成（带丰富执行过程可视化数据）
export function mockReply(input: string): { content: string; steps: Step[] } {
  const lower = input.toLowerCase();

  if (lower.includes('销售') || lower.includes('数据') || lower.includes('分析')) {
    return {
      content:
        '我已开始分析相关数据：\n\n1. **数据规模**：共检索到 1,286 条销售记录。\n2. **关键指标**：平均客单价 ￥328，复购率 34%。\n3. **亮点**：近一个月高价值客户贡献占比提升至 42%。\n\n是否需要我输出成图表或导出报表？',
      steps: [
        {
          nodeType: 'THOUGHT',
          nodeName: '任务理解',
          title: '解析用户意图，识别需要数据分析',
          detail:
            '用户提到了"销售/数据/分析"等关键词，属于数据分析类请求。我需要检索销售明细数据，进行指标归因，并输出结构化结论。',
          duration: 320,
          status: 'success',
        },
        {
          nodeType: 'TOOL',
          nodeName: '数据查询',
          title: '调用 query_sales 工具',
          input: '工具: query_sales\n参数: { "range": "近三个月", "dimension": "客户等级" }',
          result:
            '返回 1,286 条记录\n指标: { 平均客单价: 328, 复购率: 34%, 高价值客户占比: 42% }',
          duration: 1240,
          status: 'success',
        },
        {
          nodeType: 'TOOL',
          nodeName: '指标计算',
          title: '调用 compute_metrics 计算关键指标',
          input: '工具: compute_metrics\n参数: { "metric": ["客单价", "复购率", "贡献占比"] }',
          result: '客单价 ￥328 / 复购率 34% / 高价值贡献占比 42%',
          duration: 860,
          status: 'success',
        },
        {
          nodeType: 'RESULT',
          nodeName: '结果整理',
          title: '汇总指标并生成结构化结论',
          detail:
            '将查询与计算结果整理为分点结论，提示用户是否需要图表或报表导出。',
          duration: 210,
          status: 'success',
        },
      ],
    };
  }

  if (lower.includes('总结') || lower.includes('摘要')) {
    return {
      content:
        '我帮您完成了内容摘要：\n\n1. **背景**：材料描述了项目的整体目标。\n2. **进展**：核心模块已完成 80%。\n3. **下一步**：剩余工作聚焦在收尾与验收。',
      steps: [
        {
          nodeType: 'THOUGHT',
          nodeName: '任务理解',
          title: '理解总结请求',
          detail: '识别用户需要对内容进行摘要，确定采用分点提炼的格式。',
          duration: 280,
          status: 'success',
        },
        {
          nodeType: 'TOOL',
          nodeName: '文本解析',
          title: '调用 summarize 对内容分块提炼',
          input: '工具: summarize\n参数: { mode: "分点", max_points: 3 }',
          result: '得到背景 / 进展 / 下一步 三个要点',
          duration: 980,
          status: 'success',
        },
        {
          nodeType: 'RESULT',
          nodeName: '输出摘要',
          title: '生成结构化要点',
          detail: '将提炼出的要点整理为易于阅读的编号列表。',
          duration: 180,
          status: 'success',
        },
      ],
    };
  }

  if (lower.includes('钱') || lower.includes('预算') || lower.includes('花销') || lower.includes('成本')) {
    return {
      content:
        '我分析了您的预算使用情况：\n\n1. **总预算**：本月可用预算 ￥50,000。\n2. **已支出**：￥32,400（占比 64.8%）。\n3. **结余**：￥17,600，其中市场费用尚有较多余量。\n\n建议将剩余预算优先投入高转化渠道，需要我给出拆分建议吗？',
      steps: [
        {
          nodeType: 'THOUGHT',
          nodeName: '预算分析',
          title: '识别为预算/花销查询',
          detail: '用户询问资金使用情况，属于财务分析类请求，需要调用支出明细与预算对比工具。',
          duration: 310,
          status: 'success',
        },
        {
          nodeType: 'TOOL',
          nodeName: '支出明细查询',
          title: '调用 query_expense 查询支出明细',
          input: '工具: query_expense\n参数: { "period": "本月", "group_by": "费用类型" }',
          result: '市场 ￥18,200 / 研发 ￥9,600 / 行政 ￥8,600 / 其他 ￥0',
          duration: 1180,
          status: 'success',
        },
        {
          nodeType: 'TOOL',
          nodeName: '预算比对',
          title: '调用 compare_budget 计算预算余量',
          input: '工具: compare_budget\n参数: { "budget": 50000, "used": 32400 }',
          result: '剩余 ￥17,600 · 使用率 64.8%',
          duration: 620,
          status: 'success',
        },
        {
          nodeType: 'RESULT',
          nodeName: '结论生成',
          title: '汇总输出预算使用情况',
          detail: '将预算使用、剩余情况整理为分点说明，并主动提供后续建议。',
          duration: 190,
          status: 'success',
        },
      ],
    };
  }

  if (lower.includes('你好') || lower.includes('hello')) {
    return {
      content:
        '你好，我是你的智能助手！我可以帮你处理数据分析、内容总结、问题解答等任务，你可以直接输入你的需求。',
      steps: [
        {
          nodeType: 'THOUGHT',
          nodeName: '意图识别',
          title: '识别为用户问候',
          detail: '输入包含问候语，无需调用工具，直接给出欢迎语与能力引导。',
          duration: 150,
          status: 'success',
        },
      ],
    };
  }

  return {
    content: `收到你的问题："${input}"\n\n我已完成了任务理解、规划执行步骤，并生成了模拟回复。真实环境下将由后端 LangGraph Agent 结合工具实时完成。`,
    steps: [
      {
        nodeType: 'THOUGHT',
        nodeName: '任务理解',
        title: '解析用户输入',
        detail: `用户输入「${input}」，暂时无法匹配到模板，判断为通用问答请求，尝试走默认推理流程。`,
        duration: 260,
        status: 'success',
      },
      {
        nodeType: 'TOOL',
        nodeName: '知识检索',
        title: '调用知识库向量检索',
        input: `工具: retrieve_kb\n参数: { query: "${input}", top_k: 3 }`,
        result: '未检索到高相关度业务知识，返回兜底回答。',
        duration: 720,
        status: 'success',
      },
      {
        nodeType: 'RESULT',
        nodeName: '结果生成',
        title: '生成回答内容',
        detail: '基于检索结果与内置推理能力，组织生成对用户的最终回复。',
        duration: 190,
        status: 'success',
      },
    ],
  };
}