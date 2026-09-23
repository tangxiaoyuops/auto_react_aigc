<template>
  <div class="page-container">
    <div class="page-header">
      <el-button @click="router.back()">
        <el-icon><ArrowLeft /></el-icon>&nbsp; 返回
      </el-button>
      <h2 class="page-title">Agent配置 - {{ form.name || '加载中' }}</h2>
    </div>

    <el-card v-loading="loading">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="140px"
        label-position="left"
      >
        <!-- 基本信息 -->
        <el-divider content-position="left">基本信息</el-divider>

        <el-form-item label="Agent名称" prop="name">
          <el-input v-model="form.name" placeholder="Agent名称" />
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="2"
            placeholder="Agent功能描述"
          />
        </el-form-item>

        <el-form-item label="模型" prop="model">
          <el-select v-model="form.model" style="width: 100%">
            <el-option label="deepseek-chat" value="deepseek-chat" />
            <el-option label="GPT-4o" value="gpt-4o" />
            <el-option label="GPT-4o-mini" value="gpt-4o-mini" />
            <el-option label="Claude-3.5-Sonnet" value="claude-3-5-sonnet" />
          </el-select>
        </el-form-item>

        <!-- 高级参数 -->
        <el-divider content-position="left">运行参数</el-divider>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="温度" prop="temperature">
              <el-slider v-model="form.temperature" :min="0" :max="2" :step="0.1" show-input />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最大迭代" prop="maxIterations">
              <el-input-number v-model="form.maxIterations" :min="1" :max="50" />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 系统提示词 -->
        <el-divider content-position="left">系统提示词</el-divider>

        <el-form-item label="系统提示词" prop="systemPrompt">
          <el-input
            v-model="form.systemPrompt"
            type="textarea"
            :rows="8"
            placeholder="定义Agent的角色、行为和能力"
          />
        </el-form-item>

        <!-- 能力配置 -->
        <el-divider content-position="left">能力配置</el-divider>

        <el-form-item label="知识库">
          <div class="capability-selector">
            <el-select v-model="selectedKnowledgeId" placeholder="选择知识库" style="width: 100%">
              <el-option
                v-for="kb in allKnowledgeBases"
                :key="kb.id"
                :label="kb.name"
                :value="kb.id"
              />
            </el-select>
            <el-button type="primary" :disabled="!selectedKnowledgeId" @click="addKnowledge">
              添加
            </el-button>
          </div>
          <div class="capability-tags">
            <el-tag
              v-for="kb in form.capabilities.knowledgeBases"
              :key="kb.id"
              closable
              @close="removeKnowledge(kb.id)"
            >
              {{ kb.name }}
            </el-tag>
          </div>
        </el-form-item>
      </el-form>

      <div class="form-footer">
        <el-button type="primary" size="large" :loading="saving" @click="handleSave">
          保存配置
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { agentApi, resourceApi } from '@/api'
import { useSpaceStore } from '@/stores/space'
import type { Agent } from '@/types/agent'

const route = useRoute()
const router = useRouter()
const spaceStore = useSpaceStore()

const agentId = route.params.id as string
const loading = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  name: '',
  description: '',
  model: 'deepseek-chat',
  temperature: 0.7,
  maxIterations: 10,
  systemPrompt: '',
  capabilities: {
    knowledgeBases: [] as any[],
    skills: [] as any[],
    ontologies: [] as any[],
    subAgents: [] as any[],
  },
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入Agent名称', trigger: 'blur' }],
  model: [{ required: true, message: '请选择模型', trigger: 'change' }],
  systemPrompt: [{ required: true, message: '请输入系统提示词', trigger: 'blur' }],
}

// 所有可选知识库
const allKnowledgeBases = ref<any[]>([])
const selectedKnowledgeId = ref('')

onMounted(async () => {
  loading.value = true
  try {
    await Promise.all([loadDetail(), loadKnowledgeBases()])
  } finally {
    loading.value = false
  }
})

async function loadDetail() {
  const response: any = await agentApi.getAgentDetail(agentId)
  const agent: Agent = response
  form.name = agent.name
  form.description = agent.description
  form.model = agent.model
  form.temperature = agent.temperature ?? 0.7
  form.maxIterations = agent.maxIterations ?? 10
  form.systemPrompt = agent.systemPrompt
  form.capabilities = agent.capabilities || {
    knowledgeBases: [],
    skills: [],
    ontologies: [],
    subAgents: [],
  }
}

async function loadKnowledgeBases() {
  if (!spaceStore.currentSpaceId) return
  const response: any = await resourceApi.getResourceList(
    spaceStore.currentSpaceId,
    'knowledge_base'
  )
  allKnowledgeBases.value = response?.items || response || []
}

function addKnowledge() {
  const kb = allKnowledgeBases.value.find(k => k.id === selectedKnowledgeId.value)
  if (!kb) return
  if (form.capabilities.knowledgeBases.some(k => k.id === kb.id)) {
    ElMessage.warning('该知识库已添加')
    return
  }
  form.capabilities.knowledgeBases.push(kb)
  selectedKnowledgeId.value = ''
}

function removeKnowledge(id: string) {
  form.capabilities.knowledgeBases = form.capabilities.knowledgeBases.filter(k => k.id !== id)
}

async function handleSave() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    await agentApi.updateAgent(agentId, {
      name: form.name,
      description: form.description,
      model: form.model,
      temperature: form.temperature,
      maxIterations: form.maxIterations,
      systemPrompt: form.systemPrompt,
      capabilities: form.capabilities,
    })
    ElMessage.success('配置保存成功')
    router.back()
  } catch {
    // 错误已处理
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.form-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.capability-selector {
  display: flex;
  gap: 8px;
  width: 100%;
}

.capability-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}
</style>