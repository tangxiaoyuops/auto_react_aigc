// Resource API：对接 Control Plane /api/v1/resources
// 资源类型：kb / skill / prompt / ontology / ds / tool
import http from '../utils/request';

export type ResourceType = 'kb' | 'skill' | 'prompt' | 'ontology' | 'ds' | 'tool';

export interface ResourceItem {
  id: string;
  type: ResourceType;
  name: string;
  description?: string;
  meta: Record<string, any>;
  origin: string;
  created_at?: string;
  updated_at?: string;
}

export interface ResourceCreatePayload {
  type: ResourceType;
  name: string;
  description?: string;
  meta?: Record<string, any>;
}

export interface ResourceUpdatePayload {
  name?: string;
  description?: string;
  meta?: Record<string, any>;
}

function toItem(r: any): ResourceItem {
  return {
    id: r.id,
    type: r.type,
    name: r.name,
    description: r.description || '',
    meta: r.meta || {},
    origin: r.origin || 'custom',
    created_at: r.created_at,
    updated_at: r.updated_at,
  };
}

export const resourcesApi = {
  // 按类型列资源
  async list(type?: ResourceType, keyword?: string): Promise<ResourceItem[]> {
    const { data } = await http.get('/resources', {
      params: { type, keyword, page_size: 500 },
    });
    return (data.resources || []).map(toItem);
  },

  // 能力池（Agent 配置页添加知识库/本体/Skill/工具下拉）
  async pool(): Promise<Record<string, { id: string; name: string; description: string }[]>> {
    const { data } = await http.get('/resources/pool');
    return data;
  },

  async get(id: string): Promise<ResourceItem> {
    const { data } = await http.get(`/resources/${id}`);
    return toItem(data);
  },

  async create(payload: ResourceCreatePayload): Promise<ResourceItem> {
    const { data } = await http.post('/resources', payload);
    return toItem(data);
  },

  async update(id: string, payload: ResourceUpdatePayload): Promise<ResourceItem> {
    const { data } = await http.put(`/resources/${id}`, payload);
    return toItem(data);
  },

  async remove(id: string): Promise<void> {
    await http.delete(`/resources/${id}`);
  },
};

// 各类资源 Tab 元信息（供前端统一渲染）
export const RESOURCE_TAB_META: Record<
  ResourceType,
  { label: string; createLabel: string }
> = {
  kb: { label: '知识库', createLabel: '新建知识库' },
  skill: { label: 'Skill', createLabel: '新建Skill' },
  prompt: { label: '提示词', createLabel: '新建提示词' },
  ontology: { label: '本体', createLabel: '新建本体' },
  ds: { label: '数据源', createLabel: '新建数据源' },
  tool: { label: '工具', createLabel: '新建工具' },
};

export default resourcesApi;