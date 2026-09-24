import type { Agent } from '../types/agent';

// 初始化时可用的知识库/本体/Skill 池（供添加时选择）
export const KNOWLEDGE_POOL = [
  { id: 'kb1', name: '业务知识库', description: '平台业务规则与流程文档' },
  { id: 'kb2', name: '产品文档库', description: '产品功能说明与使用手册' },
  { id: 'kb3', name: '法规政策库', description: '行业法规与政策文件汇编' },
];

export const ONTOLOGY_POOL = [
  { id: 'on1', name: '业务本体', description: '领域概念与关系的语义模型' },
  { id: 'on2', name: '数据本体', description: '数据字段与指标语义定义' },
];

export const SKILL_POOL = [
  { id: 'sk1', name: '数据分析技能', description: '数据查询、聚合与可视化' },
  { id: 'sk2', name: '文档问答技能', description: '基于知识库的多轮问答流程' },
  { id: 'sk3', name: '报告生成技能', description: '自动生成结构化业务报告' },
];

// 示例 Agent 列表
export const SEED_AGENTS: Agent[] = [
  {
    id: 'agent1',
    name: '客服助手',
    model: 'Qwen3.5-397b-a17b',
    status: 'published',
    version: '1.0.0',
    description: '面向客户的服务型Agent，结合知识库回答业务问题',
    systemPrompt:
      '你是一名专业的智能客服助手。请基于知识库中的业务信息，耐心、准确地回答用户的问题。当用户询问法规或产品功能时，优先检索并引用知识库内容。',
    capabilities: {
      knowledgeBases: [
        { id: 'kb1', name: '业务知识库', description: '业务规则与流程文档' },
      ],
      ontologies: [
        { id: 'on1', name: '业务本体', description: '业务语义模型' },
      ],
      skills: [
        { id: 'sk2', name: '文档问答技能', description: '知识库问答流程' },
      ],
      tools: [
        { id: 'tool_calculator', name: 'Calculator', description: '数学计算' },
      ],
    },
    createdAt: '2026-09-01T10:00:00',
    updatedAt: '2026-09-18T10:00:00',
  },
  {
    id: 'agent2',
    name: 'LegalRegulatoryDashboard_1',
    model: 'Qwen3.5-397b-a17b',
    status: 'draft',
    version: '0.9.0',
    description: '法规监管数据分析Agent',
    systemPrompt:
      '你是法规监管数据分析助手，负责检索并解读最新监管法规，并结合业务数据给出合规建议。',
    capabilities: {
      knowledgeBases: [
        { id: 'kb3', name: '法规政策库', description: '行业法规汇编' },
      ],
      ontologies: [],
      skills: [
        { id: 'sk1', name: '数据分析技能', description: '数据查询与可视化' },
      ],
      tools: [],
    },
    createdAt: '2026-09-15T09:00:00',
    updatedAt: '2026-09-20T09:30:00',
  },
  {
    id: 'agent3',
    name: '智能研报Agent',
    model: 'claude-3-5-sonnet',
    status: 'offline',
    version: '2.1.0',
    description: '自动生成行业研究报告的Agent',
    systemPrompt: '你是行业研究助手，负责收集信息、分析趋势并生成研究报告。',
    capabilities: {
      knowledgeBases: [],
      ontologies: [],
      skills: [
        { id: 'sk3', name: '报告生成技能', description: '结构化报告生成' },
      ],
      tools: [],
    },
    createdAt: '2026-08-20T10:00:00',
    updatedAt: '2026-09-10T10:00:00',
  },
];