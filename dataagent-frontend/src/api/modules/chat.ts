import request from '@/utils/request'

// 发送消息（非流式）
export const sendMessage = (agentId: string, data: any) => {
  return request.post(`/agents/${agentId}/chat`, data)
}

// SSE流式对话
export const streamChat = (agentId: string, data: any) => {
  return request.post(`/agents/${agentId}/chat/stream`, data, {
    responseType: 'stream',
    timeout: 300000
  })
}

// 获取对话列表
export const getSessions = (agentId: string, params?: any) => {
  return request.get(`/agents/${agentId}/sessions`, { params })
}

// 获取对话消息
export const getMessages = (sessionId: string) => {
  return request.get(`/sessions/${sessionId}/messages`)
}

// 获取执行明细
export const getExecutionDetail = (messageId: string) => {
  return request.get(`/messages/${messageId}/execution`)
}

// 创建对话会话
export const createSession = (agentId: string, title?: string) => {
  return request.post(`/agents/${agentId}/sessions`, { title })
}

// 关闭对话会话
export const closeSession = (sessionId: string) => {
  return request.put(`/sessions/${sessionId}/close`)
}