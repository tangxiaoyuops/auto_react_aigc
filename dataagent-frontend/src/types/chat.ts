// 对话相关类型定义

export interface ChatSession {
  id: string
  agentId: string
  title: string
  status: 'active' | 'closed'
  createdAt: string
  updatedAt: string
}

export interface ChatMessage {
  id: string
  sessionId: string
  role: 'user' | 'assistant' | 'system'
  content: string
  metadata?: Record<string, any>
  executionDetails?: ExecutionDetail[]
  createdAt: string
}

export interface ExecutionDetail {
  step: number
  nodeType: string
  nodeName: string
  input: any
  output: any
  durationMs: number
  tokensUsed: number
  model?: string
  status: 'success' | 'failed' | 'skipped'
  errorMessage?: string
}

// SSE事件类型
export interface AgentEvent {
  type: string
  timestamp: number
  data: any
}

export enum EventType {
  RUN_START = 'RUN_START',
  RUN_END = 'RUN_END',
  RUN_ERROR = 'RUN_ERROR',
  NODE_START = 'NODE_START',
  NODE_END = 'NODE_END',
  NODE_ERROR = 'NODE_ERROR',
  TOOL_CALL_START = 'TOOL_CALL_START',
  TOOL_CALL_ARGS = 'TOOL_CALL_ARGS',
  TOOL_RESULT = 'TOOL_RESULT',
  KNOWLEDGE_SEARCH_START = 'KNOWLEDGE_SEARCH_START',
  KNOWLEDGE_SEARCH_RESULT = 'KNOWLEDGE_SEARCH_RESULT',
  SUB_AGENT_START = 'SUB_AGENT_START',
  SUB_AGENT_END = 'SUB_AGENT_END',
  TEXT_MESSAGE_START = 'TEXT_MESSAGE_START',
  TEXT_MESSAGE_CONTENT = 'TEXT_MESSAGE_CONTENT',
  TEXT_MESSAGE_END = 'TEXT_MESSAGE_END',
  THOUGHT = 'THOUGHT',
  OBSERVATION = 'OBSERVATION'
}