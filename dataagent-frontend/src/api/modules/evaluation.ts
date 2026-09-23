import request from '@/utils/request'

// 获取数据集列表
export const getDatasetList = (spaceId: string, params?: any) => {
  return request.get(`/spaces/${spaceId}/eval-datasets`, { params })
}

// 创建数据集
export const createDataset = (data: any) => {
  return request.post('/eval-datasets', data)
}

// 获取数据集用例
export const getDatasetCases = (datasetId: string) => {
  return request.get(`/eval-datasets/${datasetId}/cases`)
}

// 添加用例
export const addCases = (datasetId: string, cases: any[]) => {
  return request.post(`/eval-datasets/${datasetId}/cases`, { cases })
}

// 创建评测任务
export const createEvalTask = (data: any) => {
  return request.post('/eval-tasks', data)
}

// 获取评测任务列表
export const getEvalTaskList = (spaceId: string, params?: any) => {
  return request.get(`/spaces/${spaceId}/eval-tasks`, { params })
}

// 获取评测任务详情
export const getEvalTaskDetail = (taskId: string) => {
  return request.get(`/eval-tasks/${taskId}`)
}

// 获取评测报告
export const getEvalReport = (taskId: string) => {
  return request.get(`/eval-tasks/${taskId}/report`)
}

// 删除评测任务
export const deleteEvalTask = (taskId: string) => {
  return request.delete(`/eval-tasks/${taskId}`)
}