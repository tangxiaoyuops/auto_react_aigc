import request from '@/utils/request'
import type { Agent, AgentListItem, CreateAgentParams, UpdateAgentParams } from '@/types/agent'

// 获取Agent列表
export const getAgentList = (spaceId: string, params?: any) => {
  return request.get(`/spaces/${spaceId}/agents`, { params })
}

// 获取Agent详情
export const getAgentDetail = (agentId: string) => {
  return request.get(`/agents/${agentId}`)
}

// 创建Agent
export const createAgent = (data: CreateAgentParams) => {
  return request.post(`/spaces/${data.spaceId}/agents`, data)
}

// 更新Agent
export const updateAgent = (agentId: string, data: UpdateAgentParams) => {
  return request.put(`/agents/${agentId}`, data)
}

// 删除Agent
export const deleteAgent = (agentId: string) => {
  return request.delete(`/agents/${agentId}`)
}

// 上架Agent
export const publishAgent = (agentId: string) => {
  return request.post(`/agents/${agentId}/publish`)
}

// 下架Agent
export const offlineAgent = (agentId: string) => {
  return request.post(`/agents/${agentId}/offline`)
}

// 获取Agent能力
export const getAgentCapabilities = (agentId: string) => {
  return request.get(`/agents/${agentId}/capabilities`)
}

// 添加能力
export const addCapability = (agentId: string, data: any) => {
  return request.post(`/agents/${agentId}/capabilities`, data)
}

// 移除能力
export const removeCapability = (agentId: string, resourceId: string) => {
  return request.delete(`/agents/${agentId}/capabilities/${resourceId}`)
}

// 获取子Agent列表
export const getSubAgents = (agentId: string) => {
  return request.get(`/agents/${agentId}/sub-agents`)
}

// 添加子Agent
export const addSubAgent = (agentId: string, data: any) => {
  return request.post(`/agents/${agentId}/sub-agents`, data)
}

// 移除子Agent
export const removeSubAgent = (agentId: string, subAgentId: string) => {
  return request.delete(`/agents/${agentId}/sub-agents/${subAgentId}`)
}