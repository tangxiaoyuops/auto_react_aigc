<template>
  <div class="sidebar-container">
    <!-- 空间选择器 -->
    <div class="space-selector">
      <el-select
        v-model="currentSpaceId"
        placeholder="选择空间"
        filterable
        size="small"
        @change="onSpaceChange"
      >
        <el-option
          v-for="space in spaceStore.spaces"
          :key="space.id"
          :label="space.name"
          :value="space.id"
        />
      </el-select>
    </div>

    <!-- 导航菜单 -->
    <el-menu
      :default-active="activeMenu"
      router
      collapse-transition
      class="sidebar-menu"
    >
      <el-menu-item index="/workspace">
        <el-icon><HomeFilled /></el-icon>
        <template #title>工作台</template>
      </el-menu-item>

      <el-sub-menu index="agents">
        <template #title>
          <el-icon><Avatar /></el-icon>
          <span>Agent管理</span>
        </template>
        <el-menu-item index="/agents">Agent列表</el-menu-item>
      </el-sub-menu>

      <el-sub-menu index="resources">
        <template #title>
          <el-icon><Files /></el-icon>
          <span>资源管理</span>
        </template>
        <el-menu-item index="/resources">知识库</el-menu-item>
        <el-menu-item index="/resources?tab=skills">技能</el-menu-item>
        <el-menu-item index="/resources?tab=prompts">提示词</el-menu-item>
        <el-menu-item index="/resources?tab=data-sources">数据源</el-menu-item>
      </el-sub-menu>

      <el-menu-item index="/evaluation">
        <el-icon><DataAnalysis /></el-icon>
        <template #title>评测中心</template>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import {
  HomeFilled,
  Avatar,
  Files,
  DataAnalysis,
} from '@element-plus/icons-vue'
import { useSpaceStore } from '@/stores/space'
import { useUserStore } from '@/stores/user'
import { storeToRefs } from 'pinia'

const route = useRoute()
const spaceStore = useSpaceStore()
const userStore = useUserStore()

const { currentSpaceId } = storeToRefs(spaceStore)

const activeMenu = computed(() => {
  return route.meta.activeMenu as string || route.path
})

onMounted(() => {
  if (userStore.isLoggedIn && spaceStore.spaces.length === 0) {
    spaceStore.fetchSpaces()
  }
})

function onSpaceChange(spaceId: string) {
  spaceStore.setCurrentSpace(spaceId)
  // 切换空间后刷新数据
  window.location.reload()
}
</script>

<style scoped>
.sidebar-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-white);
}

.space-selector {
  padding: 8px;
  border-bottom: 1px solid var(--border-light);
}

.sidebar-menu {
  flex: 1;
  border-right: none;
}
</style>