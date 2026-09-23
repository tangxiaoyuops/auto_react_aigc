<template>
  <div class="app-layout">
    <!-- 侧边栏 -->
    <aside class="app-sidebar" :style="{ width: sidebarWidth }">
      <Sidebar />
    </aside>

    <!-- 主区域 -->
    <div class="app-main">
      <Header @toggle-sidebar="toggleSidebar" />
      <main class="page-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import Sidebar from './components/Sidebar.vue'
import Header from './components/Header.vue'

const collapsed = ref(false)
const sidebarWidth = ref('220px')

function toggleSidebar() {
  collapsed.value = !collapsed.value
  sidebarWidth.value = collapsed.value ? '64px' : '220px'
}
</script>

<style scoped>
.sidebar {
  transition: width 0.3s;
  border-right: 1px solid var(--border-color);
}
</style>