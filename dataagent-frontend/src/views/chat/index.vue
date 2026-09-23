<template>
  <div class="chat-layout">
    <!-- 左侧会话列表 -->
    <div class="session-panel">
      <div class="session-header">
        <span>会话</span>
        <el-button type="primary" size="small" @click="createNewSession">
          <el-icon><Plus /></el-icon>
        </el-button>
      </div>

      <div class="session-list">
        <div
          v-for="session in sessions"
          :key="session.id"
          class="session-item"
          :class="{ active: session.id === currentSessionId }"
          @click="selectSession(session.id)"
        >
          <div class="session-title">{{ session.title }}</div>
          <div class="session-time">{{ formatTime(session.createdAt) }}</div>
        </div>

        <el-empty v-if="sessions.length === 0" description="暂无会话" :image-size="60" />
      </div>
    </div>

    <!-- 中间对话区域 -->
    <div class="chat-panel">
      <!-- 消息列表 -->
      <div ref="messageListRef" class="message-list">
        <template v-for="msg in messages" :key="msg.id">
          <!-- 用户消息 -->
          <div class="message-row user" v-if="msg.role === 'user'">
            <div class="message-bubble user-bubble">{{ msg.content }}</div>
            <el-avatar :size="32" class="message-avatar" :style="{ backgroundColor: messageAvatarColor[0] }">
              {{ userInitial }}
            </el-avatar>
          </div>

          <!-- AI消息 -->
          <div class="message-row bot" v-else>
            <el-avatar
              :size="32"
              class="message-avatar"
              :style="{ backgroundColor: '#409eff' }"
            >
              AI
            </el-avatar>
            <div class="bot-message-content">
              <div class="message-bubble bot-bubble">{{ msg.content }}</div>

              <!-- 执行过程可视化 -->
              <div
                v-if="msg.executionDetails && msg.executionDetails.length > 0"
                class="execution-details"
              >
                <div class="execution-toggle" @click="toggleExecution(msg.id)">
                  <el-icon>
                    <ArrowDown v-if="expandedMessages.includes(msg.id)" />
                    <ArrowRight v-else />
                  </el-icon>
                  <span>执行过程 ({{ msg.executionDetails.length }} 步)</span>
                </div>

                <el-collapse-transition>
                  <div v-show="expandedMessages.includes(msg.id)">
                    <div
                      v-for="(step, index) in msg.executionDetails"
                      :key="index"
                      class="execution-step"
                    >
                      <div class="step-header">
                        <el-icon class="step-icon">
                          <Close v-if="step.status === 'failed'" style="color: #f56c6c" />
                          <Check v-else style="color: #67c23a" />
                        </el-icon>
                        <span class="step-name">{{ step.nodeName || step.nodeType }}</span>
                        <span class="step-time">{{ (step.durationMs / 1000).toFixed(2) }}s</span>
                      </div>
                      <div v-if="step.model" class="step-model">模型: {{ step.model }}</div>
                      <div v-if="step.output" class="step-output">{{ step.output }}</div>
                    </div>
                  </div>
                </el-collapse-transition>
              </div>
            </div>
          </div>
        </template>

        <!-- 加载指示器 -->
        <div v-if="isStreaming" class="streaming-indicator">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>Agent思考中...</span>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-area">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="2"
          :disabled="isStreaming"
          placeholder="输入你的问题，Enter发送，Shift+Enter换行"
          @keydown.enter.exact.prevent="handleSend"
        />
        <div class="input-actions">
          <span class="input-hint">按 Enter 发送</span>
          <el-button
            type="primary"
            :loading="isStreaming"
            :disabled="!inputMessage.trim()"
            @click="handleSend"
          >
            <el-icon><Promotion /></el-icon>&nbsp; 发送
          </el-button>
        </div>
      </div>
    </div>

    <!-- 右侧Agent信息 -->
    <div class="agent-panel">
      <div class="agent-header">
        <el-avatar :size="48" class="agent-info-avatar">{{ agentName.charAt(0) }}</el-avatar>
        <div class="agent-info">
          <div class="agent-name">{{ agentName }}</div>
          <div class="agent-model">{{ agent?.model || '' }}</div>
        </div>
      </div>

      <el-divider />

      <div class="agent-section-title">Agent信息</div>
      <div class="agent-desc">{{ agent?.description || '暂无描述' }}</div>

      <div class="agent-section-title">能力配置</div>
      <div class="capability-list">
        <div class="capability-item">
          <span>知识库</span>
          <el-tag size="small">{{ capabilityCount.knowledgeBases }}</el-tag>
        </div>
        <div class="capability-item">
          <span>技能</span>
          <el-tag size="small">{{ capabilityCount.skills }}</el-tag>
        </div>
        <div class="capability-item">
          <span>子Agent</span>
          <el-tag size="small">{{ capabilityCount.subAgents }}</el-tag>
        </div>
      </div>

      <el-divider />

      <div class="agent-section-title">会话统计</div>
      <div class="capability-item">
        <span>本会话消息数</span>
        <el-tag size="small">{{ messages.length }}</el-tag>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  Plus,
  Promotion,
  ArrowDown,
  ArrowRight,
  Check,
  Close,
  Loading,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { agentApi, chatApi } from '@/api'
import type { ChatMessage, ChatSession, ExecutionDetail } from '@/types/chat'

const route = useRoute()
const agentId = route.params.id as string

// Agent信息
const agent = ref<any>(null)
const agentName = computed(() => agent.value?.name || 'Agent')

// 会话
const sessions = ref<ChatSession[]>([])
const currentSessionId = ref('')

// 消息
const messages = ref<ChatMessage[]>([])
const inputMessage = ref('')
const isStreaming = ref(false)
const messageListRef = ref<HTMLElement>()

// 展开的执行详情
const expandedMessages = ref<string[]>([])

const messageAvatarColor = ['#67c23a', '#e6a23c', '#f56c6c', '#909399']

const capabilityCount = computed(() => {
  return {
    knowledgeBases: agent.value?.capabilities?.knowledgeBases?.length || 0,
    skills: agent.value?.capabilities?.skills?.length || 0,
    subAgents: agent.value?.capabilities?.subAgents?.length || 0,
  }
})

onMounted(async () => {
  await loadAgent()
  await loadSessions()
})

async function loadAgent() {
  try {
    const response: any = await agentApi.getAgentDetail(agentId)
    agent.value = response
  } catch {
    agent.value = { name: 'Agent', model: '', description: '' }
  }
}

async function loadSessions() {
  try {
    const response: any = await chatApi.getSessions(agentId)
    sessions.value = response?.items || response || []
    if (sessions.value.length > 0) {
      await selectSession(sessions.value[0].id)
    }
  } catch {
    sessions.value = []
  }
}

async function createNewSession() {
  try {
    const session: any = await chatApi.createSession(agentId, '新会话')
    sessions.value.unshift(session)
    await selectSession(session.id)
  } catch {
    ElMessage.error('创建会话失败')
  }
}

async function selectSession(sessionId: string) {
  currentSessionId.value = sessionId
  try {
    const response: any = await chatApi.getMessages(sessionId)
    messages.value = response?.items || response || []
    scrollToBottom()
  } catch {
    messages.value = []
  }
}

async function handleSend() {
  const content = inputMessage.value.trim()
  if (!content || isStreaming.value) return
  if (!currentSessionId.value) {
    await createNewSession()
  }

  // 添加用户消息
  const userMsg: ChatMessage = {
    id: `local-${Date.now()}`,
    sessionId: currentSessionId.value,
    role: 'user',
    content,
    createdAt: new Date().toISOString(),
  }
  messages.value.push(userMsg)
  inputMessage.value = ''

  // 添加占位AI消息
  const aiMsg: ChatMessage = {
    id: `ai-${Date.now()}`,
    sessionId: currentSessionId.value,
    role: 'assistant',
    content: '',
    executionDetails: [],
    createdAt: new Date().toISOString(),
  }
  messages.value.push(aiMsg)

  isStreaming.value = true
  scrollToBottom()

  try {
    const response: any = await chatApi.sendMessage(agentId, {
      sessionId: currentSessionId.value,
      message: content,
    })

    aiMsg.content = response.answer || response.content || '（无回答）'
    aiMsg.executionDetails = response.executionDetails || response.steps || []
  } catch (error: any) {
    aiMsg.content = `请求失败: ${error.message || '网络错误'}`
  } finally {
    isStreaming.value = false
    scrollToBottom()
  }
}

async function toggleExecution(msgId: string) {
  const index = expandedMessages.value.indexOf(msgId)
  if (index >= 0) {
    expandedMessages.value.splice(index, 1)
  } else {
    expandedMessages.value.push(msgId)
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}

function formatTime(time: string) {
  if (!time) return '-'
  const date = new Date(time)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const userInitial = computed(() => 'U')
</script>

<style scoped>
.chat-layout {
  display: flex;
  height: 100%;
  margin: -16px;
}

.session-panel {
  width: 240px;
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  background: var(--bg-white);
}

.session-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  font-weight: 600;
  border-bottom: 1px solid var(--border-light);
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-item {
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 4px;

  &:hover {
    background: var(--bg-page);
  }

  &.active {
    background: #ecf5ff;
  }
}

.session-title {
  font-size: 13px;
  color: var(--text-primary);
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-time {
  font-size: 11px;
  color: var(--text-secondary);
}

.chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-white);
  padding: 16px;
  height: calc(100vh - var(--header-height) - 32px);
  overflow: hidden;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.message-row.user {
  justify-content: flex-start;
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
}

.message-bubble {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.bot-bubble {
  background: var(--bg-page);
  color: var(--text-primary);
}

.user-bubble {
  background: var(--primary-color);
  color: #fff;
}

.bot-message-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
  max-width: 100%;
}

.execution-details {
  margin-top: 4px;
}

.execution-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--primary-color);
  cursor: pointer;
}

.execution-step {
  background: var(--bg-page);
  border: 1px solid var(--border-light);
  border-radius: 6px;
  padding: 8px 12px;
  margin-top: 8px;
  font-size: 12px;
}

.step-header {
  display: flex;
  align-items: center;
  gap: 6px;
}

.step-index {
  font-weight: 500;
  margin-right: auto;
}

.step-time {
  color: var(--text-secondary);
}

.step-model {
  margin-top: 4px;
  color: var(--text-secondary);
}

.step-output {
  margin-top: 4px;
  background: var(--bg-white);
  border-radius: 4px;
  padding: 6px 8px;
  white-space: pre-wrap;
  word-break: break-word;
}

.streaming-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-secondary);
  font-size: 13px;
  padding: 8px 0;
}

.input-area {
  padding-top: 16px;
  border-top: 1px solid var(--border-light);
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.input-hint {
  font-size: 12px;
  color: var(--text-secondary);
}

.agent-panel {
  width: 260px;
  border-left: 1px solid var(--border-color);
  padding: 16px;
  background: var(--bg-white);
  overflow-y: auto;
}

.agent-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.agent-info-avatar {
  background: var(--primary-color);
  font-size: 20px;
}

.agent-name {
  font-size: 15px;
  font-weight: 600;
}

.agent-model {
  font-size: 12px;
  color: var(--text-secondary);
}

.agent-section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-regular);
  margin-bottom: 8px;
}

.agent-desc {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 12px;
  line-height: 1.6;
}

.capability-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.capability-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: var(--text-regular);
}
</style>