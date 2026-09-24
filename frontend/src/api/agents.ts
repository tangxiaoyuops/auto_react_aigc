// Agent API：对接 Control Plane /api/v1/agents
import http from '../utils/request';
import type { Agent, AgentTool } from '../types/agent';

// 后端 Agent 字段 → 前端 Agent 字段
interface ApiAgent {
  id: string;
  name: string;
  description?: string;
  model: string;
  system_prompt?: string;
  prompt_resource_id?: string;
  status: string; // draft/published/archived -> 前端 offline 映射
  version: number;
  temperature: number;
  max_iterations: number;
  timeout: number;
  greeting?: string;
  suggestion_questions?: string[];
  knowledge_ids?: string[];
  ontology_ids?: string[];
  skill_ids?: string[];
  tool_ids?: string[];
  created_at: string;
  updated_at?: string;
}

function toFrontend(a: ApiAgent): Agent {
  // 后端 archived 映射为前端 offline（列表页显示"已下线"）
  const status = a.status === 'archived' ? 'offline' : (a.status as Agent['status']);
  const capTools: AgentTool[] = (a.tool_ids || []).map((id) => {
    const n = id.replace(/^tool_/, '');
    return { id, name: n, description: `工具 ${n}` };
  });
  return {
    id: a.id,
    name: a.name,
    model: a.model,
    status,
    version: `${a.version || 1}`,
    description: a.description || '',
    systemPrompt: a.system_prompt || '',
    promptResourceId: a.prompt_resource_id,
    capabilities: {
      knowledgeBases: (a.knowledge_ids || []).map((id) => ({ id, name: `知识库 ${id}`, description: '' })),
      ontologies: (a.ontology_ids || []).map((id) => ({ id, name: `本体 ${id}`, description: '' })),
      skills: (a.skill_ids || []).map((id) => ({ id, name: `Skill ${id}`, description: '' })),
      tools: capTools,
    },
    createdAt: a.created_at,
    updatedAt: a.updated_at || a.created_at,
  };
}

function toBackend(agent: Partial<Agent>): Record<string, unknown> {
  // 前端 Agent -> 后端创建/更新 payload
  return {
    name: agent.name,
    description: agent.description,
    model: agent.model,
    system_prompt: agent.systemPrompt,
    prompt_resource_id: agent.promptResourceId || null,
    // 前端 status 无 archived，offline 视为未发布
    status: agent.status === 'offline' ? 'draft' : agent.status,
    // 能力关联：保存时带上明确挂载的工具
    tool_ids: agent.capabilities?.tools?.map((t) => t.id) ?? undefined,
    skill_ids: agent.capabilities?.skills?.map((s) => s.id) ?? undefined,
    knowledge_ids: undefined,
    ontology_ids: undefined,
  };
}

export const agentApi = {
  // 列表（含统计）
  async list(params?: { keyword?: string; status?: string }): Promise<Agent[]> {
    const { data } = await http.get('/agents', { params });
    return (data.agents || []).map(toFrontend);
  },

  async stats(): Promise<{ total: number; published: number; draft: number }> {
    const { data } = await http.get('/agents/stats');
    return data;
  },

  async get(id: string): Promise<Agent> {
    const { data } = await http.get(`/agents/${id}`);
    return toFrontend(data);
  },

  async create(agent: Partial<Agent>): Promise<Agent> {
    const { data } = await http.post('/agents', toBackend(agent));
    return toFrontend(data);
  },

  async update(id: string, agent: Partial<Agent>): Promise<Agent> {
    const { data } = await http.put(`/agents/${id}`, toBackend(agent));
    return toFrontend(data);
  },

  async remove(id: string): Promise<void> {
    await http.delete(`/agents/${id}`);
  },

  async publish(id: string): Promise<Agent> {
    const { data } = await http.post(`/agents/${id}/publish`);
    return toFrontend(data);
  },

  async unpublish(id: string): Promise<Agent> {
    const { data } = await http.post(`/agents/${id}/unpublish`);
    return toFrontend(data);
  },
};

export default agentApi;