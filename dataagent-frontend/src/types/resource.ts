// 资源相关类型定义

export type ResourceType = 'knowledge_base' | 'skill' | 'prompt' | 'data_source' | 'ontology'

export interface Resource {
  id: string
  spaceId: string
  name: string
  description: string
  type: ResourceType
  config: Record<string, any>
  status: 'active' | 'disabled'
  version: string
  createdAt: string
  updatedAt: string
}

export interface KnowledgeBase {
  id: string
  name: string
  description: string
  documentCount: number
  chunkCount: number
  status: string
  createdAt: string
  updatedAt: string
}

export interface Skill {
  id: string
  name: string
  description: string
  version: string
  category: string
  requiredTools: string[]
  status: string
  createdAt: string
  updatedAt: string
}

export interface Prompt {
  id: string
  name: string
  description: string
  content: string
  category: string
  version: string
  createdAt: string
  updatedAt: string
}

export interface DataSource {
  id: string
  name: string
  description: string
  type: string
  config: Record<string, any>
  status: string
  createdAt: string
  updatedAt: string
}

export interface Ontology {
  id: string
  name: string
  description: string
  uri: string
  version: string
  createdAt: string
  updatedAt: string
}