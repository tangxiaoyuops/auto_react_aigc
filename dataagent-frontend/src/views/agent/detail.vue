<template>
  <div class="page-container">
    <div class="page-header">
      <el-button @click="router.back()">
        <el-icon><ArrowLeft /></el-icon>&nbsp; 返回
      </el-button>
      <h2 class="page-title">{{ agent?.name || 'Agent详情' }}</h2>
      <div class="header-actions">
        <el-button type="primary" @click="goChat">
          <el-icon><ChatDotRound /></el-icon>&nbsp; 对话调试
        </el-button>
        <el-button @click="goConfig">
          <el-icon><Setting /></el-icon>&nbsp; 配置
        </el-button>
      </div>
    </div>

    <el-row :gutter="16" v-if="agent">
      <!-- 基本信息 -->
      <el-col :span="24">
        <el-card class="detail-card">
          <template #header>
            <span>基本信息</span>
          </template>
          <el-descriptions :column="3" border>
            <el-descriptions-item label="名称">{{ agent.name }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="statusType(agent.status)" size="small">
                {{ statusLabel(agent.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="版本">v{{ agent.version }}</el-descriptions-item>
            <el-descriptions-item label="模型">{{ agent.model }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ formatTime(agent.createdAt) }}</el-descriptions-item>
            <el-descriptions-item label="更新时间">{{ formatTime(agent.updatedAt) }}</el-descriptions-item>
            <el-descriptions-item label="描述" :span="3">
              {{ agent.description || '暂无描述' }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>

      <!-- 系统提示词 -->
      <el-col :span="24">
        <el-card class="detail-card">
          <template #header>
            <span>系统提示词</span>
          </template>
          <pre class="prompt-content">{{ agent.systemPrompt }}</pre>
        </el-card>
      </el-col>

      <!-- 能力配置 -->
      <el-col :span="24">
        <el-card class="detail-card">
          <template #header>
            <span>能力配置</span>
          </template>

          <el-tabs>
            <el-tab-pane label="知识库">
              <div v-if="knowledgeBases.length === 0" class="empty-hint">未配置知识库</div>
              <el-tag
                v-for="kb in knowledgeBases"
                :key="kb.id"
                class="resource-tag"
                closable
                @close="removeCapability('knowledgeBases', kb.id)"
              >
                {{ kb.name }}
              </el-tag>
            </el-tab-pane>

            <el-tab-pane label="技能">
              <div v-if="skills.length === 0" class="empty-hint">未配置技能</div>
              <el-tag
                v-for="skill in skills"
                :key="skill.id"
                class="resource-tag"
                type="success"
                closable
                @close="removeCapability('skills', skill.id)"
              >
                {{ skill.name }}
              </el-tag>
            </el-tab-pane>

            <el-tab-pane label="本体知识">
              <div v-if="ontologies.length === 0" class="empty-hint">未配置本体知识</div>
              <el-tag
                v-for="onto in ontologies"
                :key="onto.id"
                class="resource-tag"
                type="warning"
                closable
                @close="removeCapability('ontologies', onto.id)"
              >
                {{ onto.name }}
              </el-tag>
            </el-tab-pane>

            <el-tab-pane label="子Agent">
              <div v-if="subAgents.length === 0" class="empty-hint">未配置子Agent</div>
              <el-table v-else :data="subAgents" stripe>
                <el-table-column prop="name" label="名称" />
                <el-table-column prop="role" label="角色" />
                <el-table-column prop="description" label="描述" />
                <el-table-column label="触发条件">
                  <template #default="{ row }">
                    <el-tag size="small">{{ row.triggerCondition }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="启用" width="80">
                  <template #default="{ row }">
                    <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
                      {{ row.enabled ? '是' : '否' }}
                    </el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, ChatDotRound, Setting } from '@element-plus/icons-vue'
import { agentApi } from '@/api'
import type { Agent } from '@/types/agent'

const route = useRoute()
const router = useRouter()

const agent = ref<Agent | null>(null)

const knowledgeBases = ref<any[]>([])
const skills = ref<any[]>([])
const ontologies = ref<any[]>([])
const subAgents = ref<any[]>([])

onMounted(async () => {
  const id = route.params.id as string
  await loadDetail(id)
})

async function loadDetail(id: string) {
  try {
    const response: any = await agentApi.getAgentDetail(id)
    agent.value = response
    if (response?.capabilities) {
      knowledgeBases.value = response.capabilities.knowledgeBases || []
      skills.value = response.capabilities.skills || []
      ontologies.value = response.capabilities.ontologies || []
      subAgents.value = response.capabilities.subAgents || []
    }
  } catch {
    agent.value = null
  }
}

async function removeCapability(category: string, id: string) {
  try {
    const agentId = route.params.id as string
    await agentApi.removeCapability(agentId, id)
    if (category === 'knowledgeBases') {
      knowledgeBases.value = knowledgeBases.value.filter(k => k.id !== id)
    } else if (category === 'skills') {
      skills.value = skills.value.filter(s => s.id !== id)
    } else if (category === 'ontologies') {
      ontologies.value = ontologies.value.filter(o => o.id !== id)
    }
  } catch {
    // 错误已处理
  }
}

function statusType(status: string) {
  switch (status) {
    case 'published': return 'success'
    case 'draft': return 'info'
    case 'offline': return 'warning'
    default: return 'info'
  }
}

function statusLabel(status: string) {
  switch (status) {
    case 'published': return '已发布'
    case 'draft': return '草稿'
    case 'offline': return '已下架'
    default: return status
  }
}

function formatTime(time: string) {
  if (!time) return '-'
  return new Date(time).toLocaleString()
}

function goChat() {
  router.push(`/agents/${route.params.id}/chat`)
}

function goConfig() {
  router.push(`/agents/${route.params.id}/config`)
}
</script>

<style scoped>
.header-actions {
  display: flex;
  gap: 8px;
}

.detail-card {
  margin-bottom: 16px;
}

.system-prompt {
  white-space: pre-wrap;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-regular);
  background: var(--bg-page);
  padding: 12px;
  border-radius: 6px;
}

.empty-hint {
  color: var(--text-secondary);
  font-size: 13px;
  padding: 12px 0;
}

.resource-tag {
  margin-right: 8px;
  margin-bottom: 8px;
}
</style>