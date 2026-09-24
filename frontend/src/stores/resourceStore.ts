// Resource 状态管理：对接后端 /resources，后端不可达时回退本地 mock
import { create } from 'zustand';
import resourcesApi, { ResourceItem, ResourceType } from '../api/resources';
import { KNOWLEDGE_POOL, ONTOLOGY_POOL, SKILL_POOL } from '../mock/agents';

interface ResourceState {
  byType: Record<ResourceType, ResourceItem[]>;
  loaded: Record<ResourceType, boolean>;
  loading: boolean;
  pool: Record<string, { id: string; name: string; description: string }[]>;
  fetchByType: (type: ResourceType) => Promise<void>;
  fetchPool: () => Promise<void>;
  createResource: (payload: {
    type: ResourceType;
    name: string;
    description?: string;
    meta?: Record<string, any>;
  }) => Promise<void>;
  updateResource: (
    id: string,
    payload: { name?: string; description?: string; meta?: Record<string, any> }
  ) => Promise<void>;
  deleteResource: (type: ResourceType, id: string) => Promise<void>;
  reset: (type: ResourceType) => void;
}

// 离线兜底数据（与后端 /resources/pool 一致）
function toOffline(type: ResourceType): ResourceItem[] {
  const mk = (rows: { id: string; name: string; description: string }[]): ResourceItem[] =>
    rows.map((r) => ({ id: r.id, type, name: r.name, description: r.description, meta: {}, origin: 'seed' }));
  switch (type) {
    case 'kb':
      return mk(KNOWLEDGE_POOL);
    case 'skill':
      return mk(SKILL_POOL);
    case 'ontology':
      return mk(ONTOLOGY_POOL);
    case 'prompt':
      return [
        { id: 'p1', type, name: '通用客服提示词', description: '面向客户的通用问答提示词模板', meta: { version: 'v1.5' }, origin: 'seed' },
        { id: 'p2', type, name: '数据分析提示词', description: '数据分析场景专属提示词', meta: { version: 'v1.2' }, origin: 'seed' },
      ];
    case 'ds':
      return [
        { id: 'ds1', type, name: '业务数仓 DWS', description: '企业业务数据仓库', meta: { type: 'ClickHouse' }, origin: 'seed' },
        { id: 'ds2', type, name: '法规政策库', description: '法规政策数据接入源', meta: { type: 'PostgreSQL' }, origin: 'seed' },
      ];
    case 'tool':
      return [
        { id: 'tool_calculator', type, name: 'Calculator', description: '数学表达式精确计算', meta: {}, origin: 'seed' },
        { id: 'tool_web_search', type, name: 'Web Search', description: '联网搜索信息', meta: {}, origin: 'seed' },
      ];
    default:
      return [];
  }
}

export const useResourceStore = create<ResourceState>((set, get) => ({
  byType: {
    kb: [],
    skill: [],
    prompt: [],
    ontology: [],
    ds: [],
    tool: [],
  },
  loaded: { kb: false, skill: false, prompt: false, ontology: false, ds: false, tool: false },
  loading: false,
  pool: {},

  fetchPool: async () => {
    try {
      const pool = await resourcesApi.pool();
      set({ pool });
    } catch (e) {
      console.warn('fetchPool failed, fallback to builtin:', e);
      set({
        pool: {
          knowledge: toOffline('kb').map((i) => ({ id: i.id, name: i.name, description: i.description || '' })),
          skill: toOffline('skill').map((i) => ({ id: i.id, name: i.name, description: i.description || '' })),
          ontology: toOffline('ontology').map((i) => ({ id: i.id, name: i.name, description: i.description || '' })),
          tool: toOffline('tool').map((i) => ({ id: i.id, name: i.name, description: i.description || '' })),
        },
      });
    }
  },

  fetchByType: async (type) => {
    if (get().loaded[type]) return;
    set({ loading: true });
    try {
      const items = await resourcesApi.list(type);
      set((s) => ({
        byType: { ...s.byType, [type]: items },
        loaded: { ...s.loaded, [type]: true },
      }));
    } catch (e) {
      console.warn(`fetch resources ${type} failed, fallback to local:`, e);
      set((s) => ({
        byType: { ...s.byType, [type]: toOffline(type) },
        loaded: { ...s.loaded, [type]: true },
      }));
    } finally {
      set({ loading: false });
    }
  },

  createResource: async (payload) => {
    try {
      const created = await resourcesApi.create(payload);
      set((s) => ({
        byType: { ...s.byType, [payload.type]: [created, ...s.byType[payload.type]] },
        loaded: { ...s.loaded, [payload.type]: true },
      }));
    } catch (e) {
      console.warn('createResource failed, fallback to local:', e);
      const local: ResourceItem = {
        id: `local_${Date.now()}`,
        type: payload.type,
        name: payload.name,
        description: payload.description || '',
        meta: payload.meta || {},
        origin: 'custom',
      };
      set((s) => ({
        byType: { ...s.byType, [payload.type]: [local, ...s.byType[payload.type]] },
        loaded: { ...s.loaded, [payload.type]: true },
      }));
    }
  },

  updateResource: async (id, payload) => {
    try {
      await resourcesApi.update(id, payload);
    } catch (e) {
      console.warn('updateResource failed, fallback to local:', e);
    }
    set((s) => ({
      byType: Object.fromEntries(
        (Object.keys(s.byType) as ResourceType[]).map((t) => [
          t,
          s.byType[t].map((item) =>
            item.id === id ? { ...item, ...payload, meta: payload.meta || item.meta } : item
          ),
        ])
      ) as Record<ResourceType, ResourceItem[]>,
    }));
  },

  deleteResource: async (type, id) => {
    try {
      await resourcesApi.remove(id);
    } catch (e) {
      console.warn('deleteResource failed, fallback to local:', e);
    }
    set((s) => ({
      byType: { ...s.byType, [type]: s.byType[type].filter((i) => i.id !== id) },
    }));
  },

  reset: (type) => {
    set((s) => ({ byType: { ...s.byType, [type]: [] }, loaded: { ...s.loaded, [type]: false } }));
  },
}));