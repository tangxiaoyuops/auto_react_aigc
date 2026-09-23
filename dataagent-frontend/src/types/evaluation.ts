// 评测相关类型定义

export interface EvalDataset {
  id: string
  spaceId: string
  name: string
  description: string
  metrics: string[]
  caseCount: number
  status: 'active' | 'disabled'
  createdAt: string
  updatedAt: string
}

export interface EvalCase {
  id: string
  datasetId: string
  question: string
  expectedAnswer: string
  category?: string
  metadata?: Record<string, any>
}

export interface EvalTask {
  id: string
  spaceId: string
  agentId: string
  datasetId: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  totalCases: number
  completedCases: number
  createdAt: string
  startedAt?: string
  completedAt?: string
}

export interface EvalReport {
  taskId: string
  agentId: string
  agentName: string
  overallScore: number
  metrics: {
    accuracy: number
    relevance: number
    fluency: number
    completeness: number
  }
  totalCases: number
  passedCases: number
  failedCases: number
  passRate: number
  avgDurationMs: number
  totalTokens: number
  caseResults: EvalCaseResult[]
  createdAt: string
}

export interface EvalCaseResult {
  caseId: string
  question: string
  expectedAnswer: string
  actualAnswer: string
  score: number
  durationMs: number
  status: 'passed' | 'failed' | 'error'
  errorMessage?: string
}