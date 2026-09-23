// 领域空间类型定义

export interface Space {
  id: string
  name: string
  description: string
  ownerId: string
  ownerName: string
  memberCount: number
  agentCount: number
  status: 'active' | 'archived'
  createdAt: string
  updatedAt: string
}

export interface SpaceMember {
  id: string
  spaceId: string
  userId: string
  username: string
  role: 'owner' | 'admin' | 'member'
  joinedAt: string
}

export interface User {
  id: string
  email: string
  username: string
  roles: string[]
  isActive: boolean
}