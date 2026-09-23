import { create } from 'zustand';
import type { Agent } from '../types/agent';
import agentApi from '../api/agents';
import { SEED_AGENTS } from '../mock/agents';

interface AgentState {
  agents: Agent[];
  loading: boolean;
  loaded: boolean;
  // 异步操作
  fetchAgents: () => Promise<void>;
  addAgent: (agent: Agent) => Promise<Agent>;
  updateAgent: (id: string, data: Partial<Agent>) => Promise<void>;
  deleteAgent: (id: string) => Promise<void>;
  publishAgent: (id: string) => Promise<void>;
  offlineAgent: (id: string) => Promise<void>;
}

let nextId = 100;

export const useAgentStore = create<AgentState>((set, get) => ({
  agents: SEED_AGENTS,
  loading: false,
  loaded: false,

  // 从后端加载 Agent 列表（首次成功后替换 seed）
  fetchAgents: async () => {
    if (get().loaded) return;
    set({ loading: true });
    try {
      const agents = await agentApi.list();
      if (agents.length > 0) {
        set({ agents, loaded: true });
      }
    } catch (e) {
      // 后端不可达时保留 mock 数据（离线兜底）
      console.warn('fetchAgents failed, fallback to mock:', e);
      set({ loaded: true });
    } finally {
      set({ loading: false });
    }
  },

  addAgent: async (agent) => {
    try {
      const created = await agentApi.create({ name: agent.name, description: agent.description, model: agent.model, systemPrompt: agent.systemPrompt });
      set((state) => {
        const filtered = state.agents.filter((a) => a.id !== agent.id);
        return { agents: [created, ...filtered] };
      });
      return created;
    } catch (e) {
      console.warn('addAgent failed, fallback to local:', e);
      const local = { ...agent, id: `agent-${++nextId}` };
      set((state) => ({ agents: [local, ...state.agents] }));
      return local;
    }
  },

  updateAgent: async (id, data) => {
    try {
      const updated = await agentApi.update(id, data);
      set((state) => ({
        agents: state.agents.map((a) =>
          a.id === id ? { ...a, ...toPartial(updated) } : a
        ),
      }));
    } catch (e) {
      console.warn('updateAgent failed, fallback to local:', e);
      set((state) => ({
        agents: state.agents.map((a) =>
          a.id === id ? { ...a, ...data, updatedAt: new Date().toISOString() } : a
        ),
      }));
    }
  },

  deleteAgent: async (id) => {
    try {
      await agentApi.remove(id);
    } catch (e) {
      console.warn('deleteAgent failed, fallback to local:', e);
    }
    set((state) => ({ agents: state.agents.filter((a) => a.id !== id) }));
  },

  publishAgent: async (id) => {
    try {
      const updated = await agentApi.publish(id);
      // updated.version 形如 "v2.0"，直接使用
      set((state) => ({
        agents: state.agents.map((a) => (a.id === id ? { ...a, status: 'published', version: updated.version } : a)),
      }));
    } catch (e) {
      console.warn('publishAgent failed, fallback to local:', e);
      set((state) => ({
        agents: state.agents.map((a) => (a.id === id ? { ...a, status: 'published' } : a)),
      }));
    }
  },

  offlineAgent: async (id) => {
    try {
      await agentApi.unpublish(id);
    } catch (e) {
      console.warn('offlineAgent failed, fallback to local:', e);
    }
    set((state) => ({
      agents: state.agents.map((a) => (a.id === id ? { ...a, status: 'offline' } : a)),
    }));
  },
}));

// 仅拷贝前端关注字段，避免覆盖 capabilities
function toPartial(agent: Agent): Partial<Agent> {
  return {
    name: agent.name,
    description: agent.description,
    model: agent.model,
    status: agent.status,
    version: agent.version,
  };
}

// 生成一个新的 Agent 占位（用于新建）
export function createNewAgent(): Agent {
  nextId += 1;
  return {
    id: `agent-${nextId}`,
    name: '新建Agent',
    model: 'Qwen3.5-397b-a17b',
    status: 'draft',
    version: '0.1.0',
    description: '',
    systemPrompt: '你是一个智能助手，请根据用户需求提供专业的帮助。',
    capabilities: {
      knowledgeBases: [],
      ontologies: [],
      skills: [],
    },
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
}