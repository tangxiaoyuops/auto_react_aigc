<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">评测中心</h2>
    </div>

    <el-tabs v-model="activeTab">
      <!-- 评测任务 -->
      <el-tab-pane label="评测任务" name="tasks">
        <div class="toolbar">
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>&nbsp; 新建评测
          </el-button>
        </div>

        <el-table :data="tasks" v-loading="loading" stripe>
          <el-table-column prop="agentName" label="Agent" min-width="150" />
          <el-table-column prop="datasetName" label="数据集" min-width="150" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="taskStatusType(row.status)" size="small">
                {{ taskStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="进度" width="150">
            <template #default="{ row }">
              <el-progress
                :percentage="row.progress || 0"
                :status="row.status === 'failed' ? 'exception' : undefined"
                :stroke-width="8"
              />
            </template>
          </el-table-column>
          <el-table-column prop="createdAt" label="创建时间" width="160">
            <template #default="{ row }">{{ formatTime(row.createdAt) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <div class="table-actions">
                <el-button
                  v-if="row.status === 'completed'"
                  size="small"
                  link
                  type="primary"
                  @click="goReport(row.id)"
                >
                  查看报告
                </el-button>
                <el-button size="small" link type="danger" @click="handleDelete(row)">
                  删除
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 数据集管理 -->
      <el-tab-pane label="数据集" name="datasets">
        <div class="toolbar">
          <el-button type="primary" @click="showCreateDataset = true">
            <el-icon><Plus /></el-icon>&nbsp; 创建数据集
          </el-button>
        </div>

        <el-table :data="datasets" v-loading="loading" stripe>
          <el-table-column prop="name" label="名称" min-width="150" />
          <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
          <el-table-column prop="caseCount" label="用例数" width="90" />
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                {{ row.status === 'active' ? '启用' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <div class="table-actions">
                <el-button size="small" link type="primary" @click="manageCases(row)">
                  管理用例
                </el-button>
                <el-button size="small" link type="danger" @click="handleDeleteDataset(row)">
                  删除
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 新建评测任务对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建评测任务" width="480px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="选择Agent" required>
          <el-select v-model="createForm.agentId" placeholder="选择Agent" style="width: 100%">
            <el-option
              v-for="agent in agents"
              :key="agent.id"
              :label="agent.name"
              :value="agent.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="选择数据集" required>
          <el-select v-model="createForm.datasetId" placeholder="选择数据集" style="width: 100%">
            <el-option
              v-for="dataset in datasets"
              :key="dataset.id"
              :label="dataset.name"
              :value="dataset.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreateTask">
          开始评测
        </el-button>
      </template>
    </el-dialog>

    <!-- 创建数据集对话框 -->
    <el-dialog v-model="showCreateDataset" title="创建数据集" width="480px">
      <el-form ref="datasetFormRef" :model="datasetForm" :rules="datasetRules" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="datasetForm.name" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="datasetForm.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDataset = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreateDataset">
          创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { agentApi, evaluationApi } from '@/api'
import { useSpaceStore } from '@/stores/space'

const router = useRouter()
const spaceStore = useSpaceStore()

const activeTab = ref('tasks')
const loading = ref(false)
const creating = ref(false)

const tasks = ref<any[]>([])
const datasets = ref<any[]>([])
const agents = ref<any[]>([])

const showCreateDialog = ref(false)
const showCreateDataset = ref(false)
const datasetFormRef = ref()

const createForm = reactive({
  agentId: '',
  datasetId: '',
})

const datasetForm = reactive({
  name: '',
  description: '',
})

const datasetRules = {
  name: [{ required: true, message: '请输入数据集名称', trigger: 'blur' }],
}

onMounted(async () => {
  await Promise.all([loadTasks(), loadDatasets(), loadAgents()])
})

async function loadTasks() {
  if (!spaceStore.currentSpaceId) return
  loading.value = true
  try {
    const response: any = await evaluationApi.getEvalTaskList(spaceStore.currentSpaceId)
    tasks.value = response?.items || response || []
  } catch {
    tasks.value = []
  } finally {
    loading.value = false
  }
}

async function loadDatasets() {
  if (!spaceStore.currentSpaceId) return
  try {
    const response: any = await evaluationApi.getDatasetList(spaceStore.currentSpaceId)
    datasets.value = response?.items || response || []
  } catch {
    datasets.value = []
  }
}

async function loadAgents() {
  if (!spaceStore.currentSpaceId) return
  try {
    const response: any = await agentApi.getAgentList(spaceStore.currentSpaceId)
    agents.value = response?.items || response || []
  } catch {
    agents.value = []
  }
}

async function handleCreateTask() {
  if (!createForm.agentId || !createForm.datasetId) {
    ElMessage.warning('请选择Agent和数据集')
    return
  }
  creating.value = true
  try {
    await evaluationApi.createEvalTask({
      spaceId: spaceStore.currentSpaceId,
      agentId: createForm.agentId,
      datasetId: createForm.datasetId,
    })
    ElMessage.success('评测任务已创建')
    showCreateDialog.value = false
    createForm.agentId = ''
    createForm.datasetId = ''
    loadTasks()
  } catch {
    // 错误已处理
  } finally {
    creating.value = false
  }
}

async function handleCreateDataset() {
  if (!datasetFormRef.value) return
  const valid = await datasetFormRef.value.validate().catch(() => false)
  if (!valid) return

  creating.value = true
  try {
    await evaluationApi.createDataset({
      spaceId: spaceStore.currentSpaceId,
      ...datasetForm,
    })
    ElMessage.success('数据集创建成功')
    showCreateDataset.value = false
    datasetForm.name = ''
    datasetForm.description = ''
    loadDatasets()
  } catch {
    // 错误已处理
  } finally {
    creating.value = false
  }
}

function manageCases(row: any) {
  // 打开用例管理（简化处理）
  ElMessage.info('用例管理功能开发中')
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm('确定删除该评测任务吗？', '提示', { type: 'warning' })
  } catch {
    return
  }
  try {
    await evaluationApi.deleteEvalTask(row.id)
    ElMessage.success('删除成功')
    loadTasks()
  } catch {
    // 错误已处理
  }
}

async function handleDeleteDataset(row: any) {
  try {
    await ElMessageBox.confirm(`确定删除数据集 "${row.name}" 吗？`, '提示', { type: 'warning' })
  } catch {
    return
  }
  try {
    await evaluationApi.deleteEvalTask(row.id)
    ElMessage.success('删除成功')
    loadDatasets()
  } catch {
    // 错误已处理
  }
}

function goReport(taskId: string) {
  router.push(`/evaluation/report/${taskId}`)
}

function taskStatusType(status: string) {
  switch (status) {
    case 'completed': return 'success'
    case 'running': return 'warning'
    case 'failed': return 'danger'
    default: return 'info'
  }
}

function taskStatusLabel(status: string) {
  switch (status) {
    case 'completed': return '已完成'
    case 'running': return '进行中'
    case 'failed': return '失败'
    default: return '待执行'
  }
}

function formatTime(time: string | undefined) {
  if (!time) return '-'
  return new Date(time).toLocaleString()
}
</script>

<style scoped>
.toolbar {
  margin-bottom: 16px;
}

.table-actions {
  display: flex;
  gap: 8px;
}
</style>