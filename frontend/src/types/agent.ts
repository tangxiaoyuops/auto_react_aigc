// Agent 相关类型定义

export interface AgentKnowledge {
  id: string;
  name: string;
  description: string;
}

export interface AgentOntology {
  id: string;
  name: string;
  description: string;
}

export interface AgentSkill {
  id: string;
  name: string;
  description: string;
}

export interface AgentTool {
  id: string;
  name: string;
  description: string;
}

export interface AgentCapabilities {
  knowledgeBases: AgentKnowledge[];
  ontologies: AgentOntology[];
  skills: AgentSkill[];
  tools: AgentTool[];
}

export interface Agent {
  id: string;
  name: string;
  model: string;
  status: 'draft' | 'published' | 'offline';
  version: string;
  description: string;
  systemPrompt: string;
  promptResourceId?: string;
  capabilities: AgentCapabilities;
  createdAt: string;
  updatedAt: string;
}

export const STATUS_LABEL: Record<Agent['status'], string> = {
  draft: '未上架',
  published: '已上架',
  offline: '已下线',
};

export const STATUS_COLOR: Record<Agent['status'], string> = {
  draft: 'default',
  published: 'success',
  offline: 'warning',
};

// 可选模型列表
export const MODEL_OPTIONS = [
  'Qwen3.5-397b-a17b',
  'Qwen3-235b-a22b',
  'gpt-4o',
  'gpt-4o-mini',
  'claude-3-5-sonnet',
  'deepseek-v3',
];