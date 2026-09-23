<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">Agent管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>&nbsp; 创建Agent
      </el-button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="el-loading" style="padding: 40px; text-align: center;">
      <el-icon class="is-loading" :size="24"><Loading /></el-icon>
    </div>

    <!-- Agent列表 -->
    <el-row v-else :gutter="16">
      <el-col v-for="agent in agents" :key="agent.id" :xs="24" :sm="12" :md="8" :lg="6">
        <el-card class="agent-card" shadow="hover">
          <div class="agent-header">
            <el-avatar :size="40" class="agent-avatar">
              {{ agent.name.charAt(0) }}
            </el-avatar>
            <el-tag :type="statusType(agent.status)" size="small">
              {{ statusLabel(agent.status) }}
            </el-tag>
          </div>

          <div class="agent-name">{{ agent.name }}</div>
          <div class="agent-desc">{{ agent.description || '暂无描述' }}</div>

          <div class="agent-meta">
            <span class="meta-item">模型: {{ agent.model || '-' }}</span>
            <span class="meta-item">版本: v{{ agent.version || '1.0' }}</span>
          </div>

          <div class="agent-actions">
            <el-button size="small" @click="goDetail(agent.id)">
              <el-icon><View /></el-icon>&nbsp; 详情
            </el-button>
            <el-button size="small" type="primary" @click="goChat(agent.id)">
              <el-icon><ChatDotRound /></el-icon>&nbsp; 对话
            </el-button>
            <el-button size="small" @click="goConfig(agent.id)">
              <el-icon><Setting /></el-icon>
            </el-button>
          </div>
        </el-card>
      </el-col>

      <!-- 空状态 -->
      <el-col v-if="agents.length === 0" :span="24">
        <el-empty description="暂无Agent，点击右上角创建">
          <el-button type="primary" @click="showCreateDialog = true">
            创建Agent
          </el-button>
        </el-empty>
      </el-col>
    </el-row>

    <!-- 分页 -->
    <div v-if="total > pageSize" class="pagination-wrapper">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="loadAgents"
      />
    </div>

    <!-- 创建Agent对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建Agent" width="520px">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="createForm.name" placeholder="Agent名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="3"
            placeholder="简要描述Agent的功能"
          />
        </el-form-item>
        <el-form-item label="模型" prop="model">
          <el-select v-model="createForm.model" placeholder="选择模型" style="width: 100%">
            <el-option label="deepseek-chat" value="deepseek-chat" />
            <el-option label="GPT-4o" value="gpt-4o" />
            <el-option label="GPT-4o-mini" value="gpt-4o-mini" />
            <el-option label="Claude-3.5-Sonnet" value="claude-3-5-sonnet" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">
          创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  Plus,
  View,
  Setting,
  ChatDotRound,
  Loading,
} from '@element-plus/icons-vue'
import { agentApi } from '@/api'
import { useSpaceStore } from '@/stores/space'
import type { AgentListItem } from '@/types/agent'

const router = useRouter()
const spaceStore = useSpaceStore()

const agents = ref<AgentListItem[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = 12
const total = ref(0)

// 创建对话框
const showCreateDialog = ref(false)
const creating = ref(false)
const createFormRef = ref<FormInstance>()
const createForm = reactive({
  name: '',
  description: '',
  model: 'deepseek-chat',
})

const createRules: FormRules = {
  name: [{ required: true, message: '请输入Agent名称', trigger: 'blur' }],
  model: [{ required: true, message: '请选择模型', trigger: 'change' }],
}

onMounted(loadAgents)

async function loadAgents() {
  if (!spaceStore.currentSpaceId) return
  loading.value = true
  try {
    const response: any = await agentApi.getAgentList(spaceStore.currentSpaceId, {
      page: page.value,
      pageSize,
    })
    agents.value = response?.items || []
    total.value = response?.total || agents.value.length
  } catch {
    agents.value = []
  } finally {
    loading.value = false
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

function goDetail(id: string) {
  router.push(`/agents/${id}`)
}

function goChat(id: string) {
  router.push(`/agents/${id}/chat`)
}

function goConfig(id: string) {
  router.push(`/agents/${id}/config`)
}

async function handleCreate() {
  if (!createFormRef.value) return
  const valid = await createFormRef.value.validate().catch(() => false)
  if (!valid) return

  creating.value = true
  try {
    await agentApi.createAgent({
      spaceId: spaceStore.currentSpaceId,
      ...createForm,
      systemPrompt: '你是一个智能助手，请根据用户需求回答问题。',
    })
    ElMessage.success('Agent创建成功')
    showCreateDialog.value = false
    loadAgents()
  } catch {
    // 错误已在拦截器处理
  } finally {
    creating.value = false
  }
}
</script>

<style scoped>
.agent-card {
  margin-bottom: 16px;

  :deep(.el-card__body) {
    padding: 16px;
  }
}

.agent-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.agent-avatar {
  background: var(--primary-color);
  font-size: 18px;
}

.agent-name {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 6px;
}

.agent-desc {
  font-size: 13px;
  color: var(--text-secondary);
  height: 40px;
  overflow: hidden;
  margin-bottom: 12px;
}

.agent-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.model-item {
  display: inline;
}

.agent-actions {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>