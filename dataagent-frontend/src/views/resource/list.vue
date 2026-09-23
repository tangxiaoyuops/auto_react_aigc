<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">资源管理</h2>
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>&nbsp; 新建{{ tabLabel }}
      </el-button>
    </div>

    <!-- 资源类型Tab -->
    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <el-tab-pane label="知识库" name="knowledge_base">
        <el-table :data="currentList" v-loading="loading" stripe>
          <el-table-column prop="name" label="名称" min-width="150">
            <template #default="{ row }">
              <el-link type="primary" @click="goDetail(row.id)">{{ row.name }}</el-link>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                {{ row.status === 'active' ? '启用' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="版本" width="80">
            <template #default="{ row }">v{{ row.version }}</template>
          </el-table-column>
          <el-table-column label="更新时间" width="160">
            <template #default="{ row }">{{ formatTime(row.updatedAt) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <div class="table-actions">
                <el-button size="small" link type="primary" @click="goDetail(row.id)">查看</el-button>
                <el-button size="small" link @click="handleDelete(row)">删除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="技能" name="skill">
        <el-table :data="currentList" v-loading="loading" stripe>
          <el-table-column prop="name" label="名称" min-width="150" />
          <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
          <el-table-column prop="category" label="分类" width="120" />
          <el-table-column label="版本" width="80">
            <template #default="{ row }">v{{ row.version }}</template>
          </el-table-column>
          <el-table-column label="更新时间" width="160">
            <template #default="{ row }">{{ formatTime(row.updatedAt) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <div class="table-actions">
                <el-button size="small" link type="primary" @click="handleEdit(row)">编辑</el-button>
                <el-button size="small" link @click="handleDelete(row)">删除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="提示词库" name="prompt">
        <el-table :data="currentList" v-loading="loading" stripe>
          <el-table-column prop="name" label="名称" min-width="150" />
          <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
          <el-table-column prop="category" label="分类" width="120" />
          <el-table-column label="版本" width="80">
            <template #default="{ row }">v{{ row.version }}</template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <div class="table-actions">
                <el-button size="small" link type="primary" @click="handleEdit(row)">编辑</el-button>
                <el-button size="small" link @click="handleDelete(row)">删除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="数据源" name="data_source">
        <el-table :data="currentList" v-loading="loading" stripe>
          <el-table-column prop="name" label="名称" min-width="150" />
          <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
          <el-table-column prop="type" label="类型" width="150" />
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
                <el-button size="small" link type="primary" @click="handleEdit(row)">编辑</el-button>
                <el-button size="small" link @click="handleDelete(row)">删除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 创建/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="560px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item v-if="form.type === 'knowledge_base'" label="知识库">
          <el-input v-model="form.config.name" placeholder="向量库名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { resourceApi } from '@/api'
import { useSpaceStore } from '@/stores/space'

const route = useRoute()
const router = useRouter()
const spaceStore = useSpaceStore()

const activeTab = ref('knowledge_base')
const loading = ref(false)
const currentList = ref<any[]>([])

// 对话框
const dialogVisible = ref(false)
const saving = ref(false)
const dialogTitle = ref('')
const isEdit = ref(false)
const formRef = ref<FormInstance>()
const editId = ref('')

const form = reactive<{
  name: string
  description: string
  type: string
  config: Record<string, any>
}>({
  name: '',
  description: '',
  type: 'knowledge_base',
  config: {},
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
}

const tabLabels: Record<string, string> = {
  knowledge_base: '知识库',
  skill: '技能',
  prompt: '提示词',
  data_source: '数据源',
}

const tabLabel = computed(() => tabLabels[activeTab.value] || '资源')

onMounted(() => {
  const tab = route.query.tab as string
  if (tab) {
    activeTab.value = tab === 'skills' ? 'skill' : (tab as string)
  }
  loadList()
})

async function handleTabChange() {
  loadList()
}

async function loadList() {
  if (!spaceStore.currentSpaceId) return
  loading.value = true
  try {
    const response: any = await resourceApi.getResourceList(spaceStore.currentSpaceId, activeTab.value)
    currentList.value = response?.items || response || []
  } catch {
    currentList.value = []
  } finally {
    loading.value = false
  }
}

function handleCreate() {
  isEdit.value = false
  dialogTitle.value = `新建${tabLabel.value}`
  form.name = ''
  form.description = ''
  form.type = activeTab.value
  form.config = {}
  dialogVisible.value = true
}

function handleEdit(row: any) {
  isEdit.value = true
  editId.value = row.id
  dialogTitle.value = `编辑${tabLabel.value}`
  form.name = row.name
  form.description = row.description
  form.type = row.type
  form.config = deepClone(row.config || {})
  dialogVisible.value = true
}

async function handleSave() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    if (isEdit.value) {
      await resourceApi.updateResource(editId.value, {
        name: form.name,
        description: form.description,
        config: form.config,
      })
      ElMessage.success('更新成功')
    } else {
      await resourceApi.createResource(spaceStore.currentSpaceId, {
        name: form.name,
        description: form.description,
        type: form.type,
        config: form.config,
      })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadList()
  } catch {
    // 错误已处理
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm(`确定删除 "${row.name}" 吗？`, '提示', {
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await resourceApi.deleteResource(row.id)
    ElMessage.success('删除成功')
    loadList()
  } catch {
    // 错误已处理
  }
}

function goDetail(id: string) {
  router.push(`/resources/${activeTab.value}/${id}`)
}

function formatTime(time: string) {
  if (!time) return '-'
  return new Date(time).toLocaleString()
}

function deepClone(obj: any): any {
  return JSON.parse(JSON.stringify(obj || {}))
}
</script>

<style scoped>
.table-actions {
  display: flex;
  gap: 8px;
}
</style>