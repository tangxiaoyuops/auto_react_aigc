<template>
  <div class="skill-editor-container">
    <!-- 顶栏 -->
    <div class="skill-editor-header">
      <el-button @click="router.back()">
        <el-icon><ArrowLeft /></el-icon>&nbsp; 返回
      </el-button>
      <div class="editor-title">
        <span class="title-text">{{ skill?.name || 'Skill' }}</span>
        <span class="title-desc">{{ skill?.description }}</span>
      </div>
      <div class="header-actions">
        <span class="save-hint" v-if="dirty">● 有未保存的修改</span>
        <el-button @click="handleAddFile">新增文件</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </div>
    </div>

    <!-- 主区：左文件树 + 右编辑 -->
    <div class="skill-editor-main">
      <!-- 左：文件树 -->
      <aside class="editor-file-tree">
        <div class="tree-title">文件</div>
        <el-input
          v-model="keyword"
          size="small"
          placeholder="筛选文件"
          clearable
          class="tree-filter"
        />
        <div class="tree-list">
          <div
            v-for="fn in filteredScripts"
            :key="fn"
            class="tree-item"
            :class="{ active: activePath === 'scripts/' + fn }"
            @click="activePath = 'scripts/' + fn"
          >
            <span class="file-icon">🐍</span>
            <span class="tree-item-name">scripts/{{ fn }}</span>
          </div>
          <div
            v-for="path in filteredDocs"
            :key="path"
            class="tree-item"
            :class="{ active: activePath === path }"
            @click="activePath = path"
          >
            <span class="file-icon">📄</span>
            <span class="tree-item-name">{{ path }}</span>
          </div>
          <div v-if="!filteredDocs.length && !filteredScripts.length" class="tree-empty">
            暂无文件，点击「新增文件」创建
          </div>
        </div>
      </aside>

      <!-- 右：编辑区 -->
      <div class="editor-body">
        <div class="editor-toolbar">
          <span class="editor-path">{{ activePath }}</span>
          <el-tag size="small" :type="isScript(activePath) ? 'warning' : 'info'" effect="plain">
            {{ isScript(activePath) ? '可执行脚本' : '文档' }}
          </el-tag>
          <div class="toolbar-spacer" />
          <el-button size="small" :icon="MagicStick" @click="handleAiEditCurrent" :disabled="!activePath || aiGenerating">
            AI 改写当前文件
          </el-button>
        </div>
        <el-input
          v-model="activeContent"
          type="textarea"
          class="editor-textarea"
          :autosize="{ minRows: 22, maxRows: 45 }"
          spellcheck="false"
        />
        <div class="editor-footer">
          <span class="editor-hint">
            文本说明装载进 Agent 上下文；scripts/*.py 可由 Agent 通过 run_skill_script 工具执行。
          </span>
          <el-button size="small" @click="handleRunScript" v-if="isScript(activePath)">
            ▶ 运行
          </el-button>
        </div>
        <el-alert
          v-if="runResult"
          :type="runResult.success ? 'success' : 'error'"
          :title="runResult.success ? '执行成功' : '执行失败'"
          :closable="false"
          class="run-result"
        >
          <pre class="run-output">{{ runResult.output }}</pre>
        </el-alert>
      </div>

      <!-- 右侧：AI 辅助面板 -->
      <aside class="ai-panel" v-if="aiPanelOpen">
        <div class="ai-panel-header">
          <span class="ai-panel-title">
            <el-icon><MagicStick /></el-icon>&nbsp; AI 辅助
          </span>
          <el-button text size="small" @click="aiPanelOpen = false">收起</el-button>
        </div>
        <div class="ai-panel-body">
          <div class="ai-field">
            <label class="ai-label">操作</label>
            <el-radio-group v-model="aiAction" size="small">
              <el-radio-button value="generate">生成全套</el-radio-button>
              <el-radio-button value="rewrite">改写/续写</el-radio-button>
            </el-radio-group>
          </div>
          <div class="ai-field">
            <label class="ai-label">
              {{ aiAction === 'generate' ? '需求描述（说明要生成的 Skill 用途）' : '改写要求（说明想怎么改）' }}
            </label>
            <el-input
              v-model="aiPrompt"
              type="textarea"
              :rows="5"
              placeholder="例：计算员工离职率统计分析，支持按部门筛选，输出分析脚本与字段说明"
            />
          </div>
          <div class="ai-actions">
            <el-button
              type="primary"
              :loading="aiGenerating"
              :icon="MagicStick"
              @click="aiAction === 'generate' ? handleAiGenerate() : handleAiRewrite()"
              style="width: 100%"
            >
              {{ aiGenerating ? 'AI 生成中...' : (aiAction === 'generate' ? 'AI 生成 Skill' : 'AI 改写') }}
            </el-button>
            <p class="ai-tip">
              生成/改写结果会合并到左侧文件树中（含 SKILL.md、scripts/*.py 等），
              确认后点击顶部「保存」落盘生效。
            </p>
          </div>
          <el-alert v-if="aiError" type="error" :title="aiError" :closable="false" class="ai-error" />
        </div>
      </aside>
      <!-- AI 面板收起时的浮出按钮 -->
      <div class="ai-collapsed" v-else @click="aiPanelOpen = true">
        <el-icon><MagicStick /></el-icon>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, MagicStick } from '@element-plus/icons-vue'
import { resourceApi } from '@/api'
import type { SkillAssistAction } from '@/api/modules/resource'

const route = useRoute()
const router = useRouter()

const skillId = route.params.id as string
const skill = ref<any>(null)
const files = reactive<Record<string, string>>({})
const saving = ref(false)
const activePath = ref('SKILL.md')
const keyword = ref('')
const runResult = ref<any>(null)

// ===== AI 辅助状态 =====
const aiPanelOpen = ref(true)          // 右侧 AI 面板是否展开
const aiAction = ref<SkillAssistAction>('generate')
const aiPrompt = ref('')               // 需求描述
const aiGenerating = ref(false)
const aiError = ref('')

// 可编辑内容与当前文件解耦，编辑时不覆盖未选中文件的临时内容
const docEdits = reactive<Record<string, string>>({})

const activeContent = computed<string>({
  get: () => docEdits[activePath.value] ?? files[activePath.value] ?? '',
  set: (v) => { docEdits[activePath.value] = v },
})

const dirty = computed(() => {
  // 有任一未保存编辑
  for (const p in docEdits) {
    if (docEdits[p] !== files[p]) return true
  }
  return false
})

const fileList = computed(() => Object.keys(files))
const scripts = computed(() =>
  fileList.value.filter((p) => p.startsWith('scripts/') && p.endsWith('.py')).map((p) => p.slice('scripts/'.length))
)
const docs = computed(() => fileList.value.filter((p) => !p.startsWith('scripts/')))
const filteredScripts = computed(() =>
  scripts.value.filter((n) => !keyword.value || n.includes(keyword.value))
)
const filteredDocs = computed(() =>
  docs.value.filter((p) => !keyword.value || p.includes(keyword.value))
)

function isScript(path: string) {
  return path.startsWith('scripts/')
}

onMounted(async () => {
  await loadSkill()
  await loadFiles()
})

async function loadSkill() {
  try {
    const res: any = await resourceApi.getResourceDetail(skillId)
    skill.value = res
  } catch {
    // 使用已缓存的列表数据
  }
}

async function loadFiles() {
  try {
    const res: any = await resourceApi.getSkillFiles(skillId)
    const tree = res?.files || {}
    for (const k in tree) {
      files[k] = tree[k]
    }
    // 若当前选中文件不存在则回退到 SKILL.md
    if (!files[activePath.value]) {
      activePath.value = files['SKILL.md'] ? 'SKILL.md' : (Object.keys(files)[0] || '')
    }
  } catch (e: any) {
    if (e?.response?.status === 400) {
      ElMessage.warning('该资源不是 Skill 类型')
    } else {
      ElMessage.error('加载 Skill 文件失败')
    }
  }
}

async function handleSave() {
  // 把当前正在编辑的内容写回 files
  if (activePath.value) files[activePath.value] = activeContent.value
  saving.value = true
  try {
    await resourceApi.updateSkillFiles(skillId, { ...files })
    // 覆盖保存后刷新文件树
    const res: any = await resourceApi.getSkillFiles(skillId)
    const tree = res?.files || {}
    for (const k in files) {
      if (!(k in tree)) delete files[k]
    }
    for (const k in tree) {
      files[k] = tree[k]
    }
    const name = files['SKILL.md']?.match(/^name:\s*(.+)$/m)?.[1]?.trim()
    if (name && skill.value) skill.value.name = name
    ElMessage.success('Skill 已保存')
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function handleAddFile() {
  try {
    const { value } = await ElMessageBox.prompt('请输入新文件名（如 references/guide.md 或 scripts/utils.py）', '新增文件', {
      confirmButtonText: '创建',
      cancelButtonText: '取消',
      inputValidator: (v: string) => (v && /^[\w\-/]+\.(md|py|txt|json)$/.test(v) ? true : '文件名不合法'),
    })
    const path = value.trim()
    if (files[path] !== undefined) {
      ElMessage.warning('文件已存在')
      return
    }
    const isScript = path.startsWith('scripts/')
    files[path] = isScript
      ? '"""\n请在下方编写可被 Agent 执行的 Python 脚本。\n"""\nimport json\nimport sys\n\n\ndef main():\n    print(json.dumps({"ok": True}))\n\n\nif __name__ == "__main__":\n    main()\n'
      : `# ${path.replace(/\.md$/, '').split('/').pop()}\n\n`
    activePath.value = path
    activeContent.value = files[path]
    ElMessage.success(`已创建 ${path}，保存后生效`)
  } catch {
    // 用户取消
  }
}

async function handleRunScript() {
  if (activeContent.value !== files[activePath.value]) {
    // 先把改动落盘再运行
    files[activePath.value] = activeContent.value
    await resourceApi.updateSkillFiles(skillId, { ...files })
  }
  const scriptName = activePath.value.slice('scripts/'.length)
  runResult.value = { success: false, output: '运行中...' }
  try {
    const execRes: any = await resourceApi.runSkillScript(skillId, scriptName)
    runResult.value = execRes
  } catch (e: any) {
    runResult.value = { success: false, output: '运行失败: ' + (e?.message || String(e)) }
  }
}

// 把 AI 生成/改写返回的文件合并进当前文件树（不落库，等待用户手动保存）
function applyAiFiles(genFiles: Record<string, string>) {
  for (const p in genFiles) {
    files[p] = genFiles[p]
  }
  // 若当前选中文件不在结果里，跳到首个生成文件
  if (!genFiles[activePath.value]) {
    const keys = Object.keys(files)
    activePath.value = keys.length ? keys[0] : ''
  }
  docEdits[activePath.value] = files[activePath.value] ?? ''
  // 从 SKILL.md 同步名称
  const md = files['SKILL.md'] || ''
  const nm = md.match(/^name:\s*(.+)$/m)?.[1]?.trim()
  if (nm && skill.value) skill.value.name = nm
}

// 生成：从需求描述生成整套 Skill 文件
async function handleAiGenerate() {
  const desc = aiPrompt.value.trim()
  if (!desc) {
    ElMessage.warning('请先描述你想要生成的 Skill 需求')
    return
  }
  aiGenerating.value = true
  aiError.value = ''
  try {
    const res: any = await resourceApi.assistSkill({
      action: 'generate',
      description: desc,
      name_hint: skill.value?.name || 'custom-skill',
    })
    applyAiFiles(res?.files || {})
    ElMessage.success('AI 已生成，请点击「保存」落盘')
  } catch (e: any) {
    aiError.value = e?.message || 'AI 生成失败'
  } finally {
    aiGenerating.value = false
  }
}

// 改写：基于当前文件集，AI 优化 target 文件（默认当前编辑文件 / all）
async function handleAiRewrite() {
  const desc = aiPrompt.value.trim()
  if (!desc && aiAction.value === 'rewrite') {
    ElMessage.warning('请描述你的改写要求')
    return
  }
  aiGenerating.value = true
  aiError.value = ''
  try {
    const res: any = await resourceApi.assistSkill({
      action: 'rewrite',
      description: desc,
      current_files: { ...files },
      target: activePath.value || 'all',
      name_hint: skill.value?.name || 'custom-skill',
    })
    applyAiFiles(res?.files || {})
    ElMessage.success('AI 已完成改写，请点击「保存」落盘')
  } catch (e: any) {
    aiError.value = e?.message || '改写失败'
  } finally {
    aiGenerating.value = false
  }
}

// 编辑区工具条：AI 续写/改写当前文件（便捷入口）
async function handleAiEditCurrent() {
  aiAction.value = 'rewrite'
  if (!aiPrompt.value) {
    aiPrompt.value = `改写并完善当前文件 ${activePath.value}，使其更专业、可直接运行`
  }
  await handleAiRewrite()
}
</script>

<style scoped>
.skill-editor-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}
.skill-editor-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.editor-title {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.title-text {
  font-size: 15px;
  font-weight: 600;
}
.title-desc {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.save-hint {
  font-size: 12px;
  color: #e6a23c;
}
.skill-editor-main {
  display: flex;
  flex: 1;
  min-height: 0;
  height: calc(100% - 60px);
}
.editor-file-tree {
  width: 240px;
  border-right: 1px solid var(--el-border-color-lighter);
  display: flex;
  flex-direction: column;
  background: #fafbfc;
}
.tree-title {
  padding: 10px 12px;
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}
.tree-filter {
  margin: 0 10px 8px;
}
.tree-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 6px;
}
.tree-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  color: var(--el-text-color-regular);
}
.tree-item:hover {
  background: #f0f1f3;
}
.tree-item.active {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  font-weight: 500;
}
.tree-item-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.file-icon {
  width: 16px;
  text-align: center;
  flex-shrink: 0;
}
.tree-empty {
  padding: 16px 8px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  text-align: center;
}
.editor-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.run-output {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  font-size: 12px;
  font-family: ui-monospace, monospace;
  max-height: 180px;
  overflow-y: auto;
}
.toolbar-spacer {
  flex: 1;
}
/* ===== AI 辅助面板 ===== */
.ai-panel {
  width: 280px;
  border-left: 1px solid var(--el-border-color-lighter);
  display: flex;
  flex-direction: column;
  background: #fcfdff;
  flex-shrink: 0;
}
.ai-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.ai-panel-title {
  display: flex;
  align-items: center;
  font-size: 13px;
  font-weight: 600;
  color: #7c3aed;
}
.ai-panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.ai-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.ai-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.ai-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.ai-tip {
  font-size: 11px;
  line-height: 1.6;
  color: var(--el-text-color-secondary);
  margin: 0;
}
.ai-error {
  flex-shrink: 0;
}
.ai-collapsed {
  width: 34px;
  flex-shrink: 0;
  border-left: 1px solid var(--el-border-color-lighter);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #7c3aed;
  background: #fafbfc;
}
.ai-collapsed:hover {
  background: #f3f4ff;
}
.editor-toolbar {
  padding: 10px 14px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  display: flex;
  align-items: center;
  gap: 8px;
}
.editor-path {
  font-size: 13px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  font-family: ui-monospace, monospace;
}
.editor-textarea {
  flex: 1;
  border: none;
}
.editor-textarea :deep(.el-textarea__inner) {
  border: none;
  border-radius: 0;
  height: 100%;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 13px;
  line-height: 1.6;
  padding: 12px 14px;
  box-shadow: none;
  resize: none;
}
.editor-footer {
  padding: 8px 14px;
  border-top: 1px solid var(--el-border-color-lighter);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.editor-hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.run-result {
  margin: 0 14px 12px;
}
.run-output {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  font-size: 12px;
  font-family: ui-monospace, monospace;
  max-height: 180px;
  overflow-y: auto;
}
</style>