import { defineStore } from 'pinia'
import request from '@/utils/request'

interface UserState {
  token: string
  userInfo: any
}

export const useUserStore = defineStore('user', {
  state: (): UserState => ({
    token: localStorage.getItem('token') || '',
    userInfo: JSON.parse(localStorage.getItem('userInfo') || 'null'),
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
  },

  actions: {
    // 登录
    async login(email: string, password: string) {
      const response: any = await request.post('/auth/login', { email, password })
      this.token = response.access_token
      this.userInfo = response.user
      localStorage.setItem('token', this.token)
      localStorage.setItem('userInfo', JSON.stringify(this.userInfo))
    },

    // 注册
    async register(data: any) {
      const response: any = await request.post('/auth/register', data)
      this.token = response.access_token
      this.userInfo = response.user
      localStorage.setItem('token', this.token)
      localStorage.setItem('userInfo', JSON.stringify(this.userInfo))
    },

    // 获取当前用户信息
    async fetchUserInfo() {
      if (!this.token) return null
      try {
        const response: any = await request.get('/users/me')
        this.userInfo = response
        localStorage.setItem('userInfo', JSON.stringify(response))
        return response
      } catch {
        return null
      }
    },

    // 退出登录
    logout() {
      this.clearToken()
    },

    clearToken() {
      this.token = ''
      this.userInfo = null
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
    },
  },
})