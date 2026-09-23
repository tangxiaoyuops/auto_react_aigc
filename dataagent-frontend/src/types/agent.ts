// Agent相关类型定义

export interface Agent {
  id: string
  spaceId: string
  name: string
  description: string
  model: string
  systemPrompt: string
  status: 'draft' | 'published' | 'offline'
  version: string
  capabilities: AgentCapabilities
  maxIterations: number
  temperature: number
  timeout: number
  createdAt: string
  updatedAt: string
  createdBy: string
}

export interface CapabilityItem {
  id: string
  name: string
  description?: string
  version?: string
  enabled: boolean
  config?: Record<string, any>
}

export interface AgentCapabilities {
  knowledgeBases: CapabilityItem[]
  ontologies: CapabilityItem[]
  skills: CapabilityItem[]
  subAgents: SubAgent[]
}

export interface SubAgent {
  id: string
  name: string
  role: string
  description?: string
  triggerCondition: string
  enabled: boolean
}

export interface AgentListItem {
  id: string
  name: string
  description: string
  model: string
  status: string
  version: string
  updatedAt: string
}

export interface CreateAgentParams {
  spaceId: string
  name: string
  description: string
  model: string
  systemPrompt: string
}

export interface UpdateAgentParams extends Partial<CreateAgentParams> {
  status?: string
  temperature?: number
  maxIterations?: number
  timeout?: number
  capabilities?: AgentCapabilities
}