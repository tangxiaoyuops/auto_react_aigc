import request from '@/utils/request'

// 获取空间列表
export const getSpaceList = (params?: any) => {
  return request.get('/spaces', { params })
}

// 获取空间详情
export const getSpaceDetail = (spaceId: string) => {
  return request.get(`/spaces/${spaceId}`)
}

// 创建空间
export const createSpace = (data: any) => {
  return request.post('/spaces', data)
}

// 更新空间
export const updateSpace = (spaceId: string, data: any) => {
  return request.put(`/spaces/${spaceId}`, data)
}

// 删除空间
export const deleteSpace = (spaceId: string) => {
  return request.delete(`/spaces/${spaceId}`)
}

// 获取空间成员
export const getSpaceMembers = (spaceId: string) => {
  return request.get(`/spaces/${spaceId}/members`)
}

// 添加成员
export const addMember = (spaceId: string, data: any) => {
  return request.post(`/spaces/${spaceId}/members`, data)
}

// 移除成员
export const removeMember = (spaceId: string, userId: string) => {
  return request.delete(`/spaces/${spaceId}/members/${userId}`)
}