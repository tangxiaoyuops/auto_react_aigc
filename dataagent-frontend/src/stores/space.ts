import { defineStore } from 'pinia'
import { spaceApi } from '@/api'
import type { Space } from '@/types/space'

interface SpaceState {
  spaces: Space[]
  currentSpaceId: string
  loading: boolean
}

export const useSpaceStore = defineStore('space', {
  state: (): SpaceState => ({
    spaces: [],
    currentSpaceId: localStorage.getItem('currentSpaceId') || '',
    loading: false,
  }),

  getters: {
    currentSpace: (state) => {
      return state.spaces.find((s) => s.id === state.currentSpaceId) || null
    },
  },

  actions: {
    async fetchSpaces() {
      this.loading = true
      try {
        const response: any = await spaceApi.getSpaceList()
        this.spaces = response?.items || response || []
        if (!this.currentSpaceId && this.spaces.length > 0) {
          this.setCurrentSpace(this.spaces[0].id)
        }
      } finally {
        this.loading = false
      }
    },

    setCurrentSpace(spaceId: string) {
      this.currentSpaceId = spaceId
      localStorage.setItem('currentSpaceId', spaceId)
    },

    async createSpace(data: any): Promise<Space> {
      const space: any = await spaceApi.createSpace(data)
      await this.fetchSpaces()
      this.setCurrentSpace(space.id)
      return space
    },
  },
})