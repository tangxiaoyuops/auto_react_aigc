<template>
  <div class="page-container workspace">
    <!-- 欢迎横幅 -->
    <div class="welcome-banner">
      <div class="welcome-text">
        <h2>欢迎回来，{{ username }}</h2>
        <p>这里是你的DataAgent工作台，开始今天的Agent开发吧</p>
      </div>
      <div class="welcome-actions">
        <el-button type="primary" @click="handleCreateAgent">
          <el-icon><Plus /></el-icon>&nbsp; 创建Agent
        </el-button>
        <el-button @click="router.push('/agents')">
          <el-icon><View /></el-icon>&nbsp; 查看全部
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stat-cards">
      <el-card class="stat-card" shadow="hover">
        <div class="stat-info">
          <div class="stat-label">Agent总数</div>
          <div class="stat-value">{{ agentCount }}</div>
        </div>
        <el-icon class="stat-icon"><Avatar /></el-icon>
      </el-card>

      <el-card class="stat-card" shadow="hover">
        <div class="stat-info">
          <div class="stat-label">资源总数</div>
          <div class="stat-value">{{ resourceCount }}</div>
        </div>
        <el-icon class="stat-icon"><Files /></el-icon>
      </el-card>

      <el-card class="stat-card" shadow="hover">
        <div class="stat-info">
          <div class="stat-label">评测任务</div>
          <div class="stat-value">{{ evalTaskCount }}</div>
        </div>
        <el-icon class="stat-icon"><DataAnalysis /></el-icon>
      </el-card>
    </div>

    <!-- 快捷功能 -->
    <div class="quick-section">
      <div class="section-header">
        <h3>快捷入口</h3>
      </div>
      <div class="quick-grid">
        <div class="quick-item" @click="router.push('/agents')">
          <el-icon class="qi-icon" color="#409eff"><Avatar /></el-icon>
          <div class="qi-name">管理Agent</div>
          <div class="qi-desc">创建和配置Agent</div>
        </div>
        <div class="quick-item" @click="router.push('/agents')">
          <el-icon class="qi-icon" color="#67c23a"><ChatDotRound /></el-icon>
          <div class="qi-name">调试对话</div>
          <div class="qi-desc">实时测试Agent</div>
        </div>
        <div class="quick-item" @click="router.push('/resources')">
          <el-icon class="qi-icon" color="#e6a23c"><Collection /></el-icon>
          <div class="qi-name">管理知识库</div>
          <div class="qi-desc">上传和管理文档</div>
        </div>
        <div class="quick-item" @click="router.push('/evaluation')">
          <el-icon class="qi-icon" color="#909399"><DataAnalysis /></el-icon>
          <div class="qi-name">评测中心</div>
          <div class="qi-desc">评估Agent性能</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  Plus,
  View,
  Avatar,
  Files,
  DataAnalysis,
  ChatDotRound,
  Collection,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { useSpaceStore } from '@/stores/space'
import { agentApi, evaluationApi } from '@/api'

const router = useRouter()
const userStore = useUserStore()
const spaceStore = useSpaceStore()

const agentCount = ref(0)
const resourceCount = ref(0)
const evalTaskCount = ref(0)

const username = computed(() => {
  return userStore.userInfo?.username || '用户'
})

onMounted(async () => {
  await loadStats()
})

async function loadStats() {
  try {
    if (spaceStore.currentSpaceId) {
      const [agents, evals] = await Promise.all([
        agentApi.getAgentList(spaceStore.currentSpaceId),
        evaluationApi.getEvalTaskList(spaceStore.currentSpaceId).catch(() => ({ items: [] })),
      ])
      const agentsData: any = agents
      const evalsData: any = evals
      agentCount.value = agentsData?.total || agentsData?.items?.length || 0
      evalTaskCount.value = evalsData?.total || evalsData?.items?.length || 0
    }
  } catch {
    // 使用默认值0
  }
}

function handleCreateAgent() {
  router.push('/agents')
}
</script>

<style scoped>
.workspace {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.welcome-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 32px;
  color: #fff;
}

.welcome-text h2 {
  font-size: 22px;
  margin-bottom: 8px;
}

.welcome-text p {
  opacity: 0.9;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.stat-card {
  display: flex;
  justify-content: space-between;
  align-items: center;

  :deep(.el-card__body) {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
  }
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-icon {
  font-size: 40px;
  color: var(--primary-color);
}

.quick-section {
  .section-header h3 {
    font-size: 16px;
    margin-bottom: 12px;
  }
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.quick-item {
  background: var(--bg-white);
  border-radius: 8px;
  padding: 20px;
  cursor: pointer;
  border: 1px solid var(--border-light);
  transition: all 0.3s;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    transform: translateY(-2px);
  }
}

.qi-icon {
  margin-bottom: 8px;
}

.qa-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 4px;
}

.qi-desc {
  font-size: 12px;
  color: var(--text-secondary);
}
</style>