<template>
  <div class="page-container">
    <div class="page-header">
      <el-button @click="router.back()">
        <el-icon><ArrowLeft /></el-icon>&nbsp; 返回
      </el-button>
      <h2 class="page-title">{{ resource?.name || '资源详情' }}</h2>
    </div>

    <el-card v-loading="loading">
      <!-- 基本信息 -->
      <el-descriptions :column="3" border>
        <el-descriptions-item label="名称">{{ resource?.name }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ typeLabel }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="resource?.status === 'active' ? 'success' : 'info'" size="small">
            {{ resource?.status === 'active' ? '启用' : '停用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="版本">v{{ resource?.version }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(resource?.createdAt) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatTime(resource?.updatedAt) }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="3">
          {{ resource?.description || '暂无描述' }}
        </el-descriptions-item>
      </el-descriptions>

      <!-- 知识库文档管理 -->
      <template v-if="isKnowledgeBase">
        <el-divider content-position="left">文档管理</el-divider>

        <div class="doc-upload">
          <el-upload
            :auto-upload="false"
            :show-file-list="false"
            :limit="10"
            accept=".txt,.md,.pdf,.docx,.json"
            @change="handleFileChange"
          >
            <el-button type="primary">
              <el-icon><Upload /></el-icon>&nbsp; 上传文档
            </el-button>
          </el-upload>
          <el-button
            type="success"
            :disabled="!selectedFile"
            :loading="uploading"
            @click="handleUpload"
          >
            开始上传
          </el-button>
          <span v-if="selectedFile" class="file-name">{{ selectedFile.name }}</span>
        </div>

        <el-table :data="documents" stripe style="margin-top: 16px">
          <el-table-column prop="filename" label="文件名" min-width="200" />
          <el-table-column prop="size" label="大小" width="100">
            <template #default="{ row }">{{ formatSize(row.size) }}</template>
          </el-table-column>
          <el-table-column prop="chunks" label="分块数" width="90" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'completed' ? 'success' : 'warning'" size="small">
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button size="small" link type="danger" @click="handleDeleteDoc(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Upload } from '@element-plus/icons-vue'
import { resourceApi } from '@/api'

const route = useRoute()
const router = useRouter()

const resourceId = route.params.id as string
const type = route.params.type as string

const loading = ref(false)
const resource = ref<any>(null)
const documents = ref<any[]>([])

const selectedFile = ref<File | null>(null)
const uploading = ref(false)

const isKnowledgeBase = computed(() => type === 'knowledge_base')

const typeLabel = computed(() => {
  const map: Record<string, string> = {
    knowledge_base: '知识库',
    skill: '技能',
    prompt: '提示词',
    data_source: '数据源',
    ontology: '本体知识',
  }
  return map[type] || type
})

onMounted(async () => {
  await loadDetail()
  if (isKnowledgeBase.value) {
    await loadDocuments()
  }
})

async function loadDetail() {
  loading.value = true
  try {
    const response: any = await resourceApi.getResourceDetail(resourceId)
    resource.value = response
  } catch {
    resource.value = null
  } finally {
    loading.value = false
  }
}

async function loadDocuments() {
  try {
    const response: any = await resourceApi.getKnowledgeDocs(resourceId)
    documents.value = response?.items || response || []
  } catch {
    documents.value = []
  }
}

function handleFileChange(file: any) {
  selectedFile.value = file.raw
}

async function handleUpload() {
  if (!selectedFile.value) return
  uploading.value = true
  try {
    await resourceApi.uploadKnowledgeDoc(resourceId, selectedFile.value)
    ElMessage.success('上传成功，正在解析...')
    selectedFile.value = null
    await loadDocuments()
  } catch {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}

async function handleDeleteDoc(row: any) {
  try {
    await ElMessageBox.confirm(`确定删除文档 "${row.filename}" 吗？`, '提示', {
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await resourceApi.deleteKnowledgeDoc(resourceId, row.id)
    ElMessage.success('删除成功')
    loadDocuments()
  } catch {
    // 错误已处理
  }
}

function formatTime(time: string | undefined) {
  if (!time) return '-'
  return new Date(time).toLocaleString()
}

function formatSize(size: number) {
  if (!size) return '-'
  if (size > 1024 * 1024) return (size / 1024 / 1024).toFixed(1) + ' MB'
  if (size > 1024) return (size / 1024).toFixed(1) + ' KB'
  return size + ' B'
}
</script>

<style scoped>
.doc-upload {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-name {
  font-size: 13px;
  color: var(--text-regular);
}
</style>