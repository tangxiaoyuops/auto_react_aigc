<template>
  <div class="page-container">
    <div class="page-header">
      <el-button @click="router.back()">
        <el-icon><ArrowLeft /></el-icon>&nbsp; 返回
      </el-button>
      <h2 class="page-title">评测报告 - {{ report?.agentName || '加载中' }}</h2>
    </div>

    <div v-loading="loading">
      <template v-if="report">
        <!-- 总体得分 -->
        <el-row :gutter="16" class="score-row">
          <el-col :span="8">
            <el-card class="score-card" shadow="hover">
              <div class="score-value" :style="{ color: scoreColor(report.overallScore) }">
                {{ report.overallScore?.toFixed(1) || 0 }}
              </div>
              <div class="score-label">综合得分</div>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card class="score-card" shadow="hover">
              <div class="score-value" :style="{ color: scoreColor(report.passRate * 100) }">
                {{ (report.passRate * 100).toFixed(0) }}%
              </div>
              <div class="score-label">通过率 ({{ report.passedCases }}/{{ report.totalCases }})</div>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card class="score-card" shadow="hover">
              <div class="score-value" style="color: #409eff">
                {{ (report.avgDurationMs / 1000).toFixed(1) }}s
              </div>
              <div class="score-label">平均响应时间</div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 分项指标 -->
        <el-card class="metrics-card">
          <template #header>
            <span>分项指标</span>
          </template>
          <el-row :gutter="20">
            <el-col v-for="metric in computedMetrics" :key="metric.key" :span="6">
              <div class="metric-item">
                <div class="metric-name">{{ metricLabel(metric.key) }}</div>
                <el-progress
                  :percentage="metric.percentage"
                  :color="scoreColor(metric.percentage)"
                  :stroke-width="12"
                />
              </div>
            </el-col>
          </el-row>
        </el-card>

        <!-- 用例明细 -->
        <el-card class="cases-card">
          <template #header>
            <span>用例明细 ({{ report.totalCases }})</span>
          </template>

          <el-table :data="report.caseResults" stripe>
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-icon>
                  <CircleCheck v-if="row.status === 'passed'" style="color: #67c23a" />
                  <CircleClose v-else style="color: #f56c6c" />
                </el-icon>
              </template>
            </el-table-column>
            <el-table-column prop="question" label="问题" min-width="200" />
            <el-table-column prop="expectedAnswer" label="预期答案" min-width="180" show-overflow-tooltip />
            <el-table-column prop="actualAnswer" label="实际答案" min-width="180" show-overflow-tooltip />
            <el-table-column label="得分" width="90">
              <template #default="{ row }">
                <span :style="{ color: scoreColor(row.score * 100) }">{{ (row.score * 100).toFixed(0) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="耗时" width="90">
              <template #default="{ row }">
                {{ (row.durationMs / 1000).toFixed(1) }}s
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </template>

      <el-empty v-else-if="!loading" description="暂无评测报告" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { evaluationApi } from '@/api'

const route = useRoute()
const router = useRouter()

const taskId = route.params.taskId as string
const loading = ref(false)
const report = ref<any>(null)

const computedMetrics = computed(() => {
  const metrics = report.value?.metrics || {}
  return Object.entries(metrics).map(([key, value]) => ({
    key,
    percentage: Number(Number(value) * 100).toFixed(0),
  }))
})

onMounted(loadReport)

async function loadReport() {
  loading.value = true
  try {
    const response: any = await evaluationApi.getEvalReport(taskId)
    report.value = response
  } catch {
    report.value = null
  } finally {
    loading.value = false
  }
}

function scoreColor(score: any) {
  const s = Number(score)
  if (s >= 80) return '#67c23a'
  if (s >= 60) return '#e6a23c'
  return '#f56c6c'
}

function metricLabel(key: string) {
  const map: Record<string, string> = {
    accuracy: '准确率',
    relevance: '相关性',
    fluency: '流畅度',
    completeness: '完整性',
  }
  return map[key] || key
}
</script>

<style scoped>
.score-row {
  margin-bottom: 16px;
}

.score-card {
  text-align: center;

  :deep(.el-card__body) {
    padding: 24px;
  }
}

.score-value {
  font-size: 40px;
  font-weight: 700;
  margin-bottom: 4px;
}

.score-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.metrics-card,
.cases-card {
  margin-bottom: 16px;
}

.metric-item {
  margin-bottom: 8px;
}

.metric-name {
  font-size: 13px;
  color: var(--text-regular);
  margin-bottom: 6px;
  text-align: center;
}
</style>