import request from '@/utils/request'

// 获取资源列表
export const getResourceList = (spaceId: string, type?: string, params?: any) => {
  return request.get(`/spaces/${spaceId}/resources`, { params: { type, ...params } })
}

// 创建资源
export const createResource = (spaceId: string, data: any) => {
  return request.post(`/spaces/${spaceId}/resources`, data)
}

// 获取资源详情
export const getResourceDetail = (resourceId: string) => {
  return request.get(`/resources/${resourceId}`)
}

// 更新资源
export const updateResource = (resourceId: string, data: any) => {
  return request.put(`/resources/${resourceId}`, data)
}

// 删除资源
export const deleteResource = (resourceId: string) => {
  return request.delete(`/resources/${resourceId}`)
}

// 知识库 - 上传文档
export const uploadKnowledgeDoc = (knowledgeId: string, file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post(`/knowledge/${knowledgeId}/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000
  })
}

// 知识库 - 获取文档列表
export const getKnowledgeDocs = (knowledgeId: string) => {
  return request.get(`/knowledge/${knowledgeId}/documents`)
}

// 知识库 - 删除文档
export const deleteKnowledgeDoc = (knowledgeId: string, docId: string) => {
  return request.delete(`/knowledge/${knowledgeId}/documents/${docId}`)
}

// 知识库 - 检索
export const searchKnowledge = (knowledgeId: string, query: string, k?: number) => {
  return request.post(`/knowledge/${knowledgeId}/search`, { query, k })
}

// ===== Skill 文件树（Cursor/Claude 风格） =====
// 获取 Skill 文件树（path -> content）
export const getSkillFiles = (skillId: string) => {
  return request.get(`/resources/skills/${skillId}/files`)
}

// 读取单个 Skill 文件
export const getSkillFile = (skillId: string, path: string) => {
  return request.get(`/resources/skills/${skillId}/files/${path}`)
}

// 整体覆盖保存 Skill 文件树
export const updateSkillFiles = (skillId: string, files: Record<string, string>) => {
  return request.put(`/resources/skills/${skillId}/files`, { files })
}

// 运行 Skill 脚本（编辑器「运行」按钮）
export const runSkillScript = (skillId: string, script: string, args?: string[]) => {
  return request.post(`/resources/skills/${skillId}/run`, { script, args: args || [] })
}

// ===== AI 辅助生成 / 改写 Skill =====
export type SkillAssistAction = 'generate' | 'rewrite'

export interface SkillAssistParams {
  action: SkillAssistAction
  description: string
  current_files?: Record<string, string>
  target?: string
  name_hint?: string
}

// 调用 AI 生成/改写 Skill 文件树内容
export const assistSkill = (params: SkillAssistParams) => {
  return request.post('/skill/assist', params)
}