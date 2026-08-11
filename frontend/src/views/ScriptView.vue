<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { request } from '../api/client'

interface Beat {
  time: string
  point: string
}

interface ScriptData {
  id: number
  project_id: number
  content: string
  beats: Beat[]
  structure: { opening: string; conflict: string; ending: string }
  awkward: { sentence: string; issues: string[] }[]
  created_at: string
}

interface EntityResult {
  characters: { name: string; description?: string }[]
  scenes: { name: string }[]
}

const route = useRoute()
const projectId = Number(route.params.id)

const projectInfo = ref<{ title: string; genre?: string } | null>(null)
const genre = ref(route.query.genre as string || '')
const theme = ref('')
const generating = ref(false)
const saving = ref(false)
const rewriting = ref(false)
const extracting = ref(false)
const rewriteInstruction = ref('')
const errorMsg = ref('')
const notice = ref('')
const script = ref<ScriptData | null>(null)
const entities = ref<EntityResult | null>(null)
const activeTab = ref<'opening' | 'conflict' | 'ending'>('opening')
const isNewProject = ref(false)

async function generate() {
  if (!genre.value.trim()) {
    errorMsg.value = '请先填写题材'
    return
  }
  generating.value = true
  errorMsg.value = ''
  notice.value = ''
  try {
    script.value = await request<ScriptData>(`/projects/${projectId}/script/generate`, {
      method: 'POST',
      body: JSON.stringify({ genre: genre.value, theme: theme.value }),
    })
    notice.value = '剧本已生成'
  } catch (e) {
    errorMsg.value = (e as Error).message
  } finally {
    generating.value = false
  }
}

async function save() {
  if (!script.value?.content.trim()) return
  saving.value = true
  errorMsg.value = ''
  notice.value = ''
  try {
    script.value = await request<ScriptData>(`/projects/${projectId}/script`, {
      method: 'PUT',
      body: JSON.stringify({ content: script.value.content }),
    })
    notice.value = '已保存'
  } catch (e) {
    errorMsg.value = (e as Error).message
  } finally {
    saving.value = false
  }
}

async function rewrite() {
  if (!rewriteInstruction.value.trim() || !script.value) return
  rewriting.value = true
  errorMsg.value = ''
  notice.value = ''
  try {
    script.value = await request<ScriptData>(`/projects/${projectId}/script/rewrite`, {
      method: 'POST',
      body: JSON.stringify({ instruction: rewriteInstruction.value }),
    })
    rewriteInstruction.value = ''
    notice.value = '改写完成'
  } catch (e) {
    errorMsg.value = (e as Error).message
  } finally {
    rewriting.value = false
  }
}

async function extract() {
  extracting.value = true
  errorMsg.value = ''
  notice.value = ''
  try {
    entities.value = await request<EntityResult>(`/projects/${projectId}/script/extract`, {
      method: 'POST',
    })
    notice.value = '角色与场景已登记到定妆库'
  } catch (e) {
    errorMsg.value = (e as Error).message
  } finally {
    extracting.value = false
  }
}

async function loadScript() {
  try {
    script.value = await request<ScriptData>(`/projects/${projectId}/script`)
  } catch {
    script.value = null
  }
  // 加载项目信息（标题、题材）
  try {
    const project = await request<{ title: string; genre?: string }>(`/projects/${projectId}`)
    projectInfo.value = project
    // 如果路由参数没有题材，使用项目存储的题材
    if (!genre.value && project.genre) {
      genre.value = project.genre
    }
  } catch {
    projectInfo.value = null
  }
}

watch(() => route.query.genre, (val) => {
  if (val && !genre.value) {
    genre.value = val as string
  }
})

watch(() => route.query.fromCreate, (val) => {
  if (val === 'true') {
    isNewProject.value = true
  }
})

onMounted(async () => {
  await loadScript()
  if (route.query.fromCreate === 'true') {
    isNewProject.value = true
  }
})
</script>

<template>
  <section class="script-page">
    <!-- 项目信息栏 -->
    <div v-if="projectInfo" class="project-header">
      <span class="project-title">{{ projectInfo.title }}</span>
      <span v-if="projectInfo.genre" class="project-genre">题材：{{ projectInfo.genre }}</span>
      <span class="project-status">· 第一步骤：剧本创作</span>
    </div>

    <div class="toolbar">
      <div class="generate-form">
        <input v-model="genre" placeholder="题材（如：霸总 / 重生 / 逆袭）" />
        <input v-model="theme" placeholder="主题（可选）" />
        <button :disabled="generating || !genre.trim()" @click="generate">
          {{ generating ? '生成中…' : '生成剧本' }}
        </button>
      </div>
      <div class="actions">
        <button class="ghost" :disabled="!script || saving" @click="save">
          {{ saving ? '保存中…' : '保存' }}
        </button>
        <button class="ghost" :disabled="!script || extracting" @click="extract">
          {{ extracting ? '抽取中…' : '抽取角色/场景' }}
        </button>
      </div>
    </div>

    <p v-if="errorMsg" class="error">{{ errorMsg }}</p>
    <p v-if="notice" class="notice">{{ notice }}</p>

    <div v-if="script" class="layout">
      <div class="editor">
        <h3>剧本正文（{{ script.content.length }} 字）</h3>
        <textarea v-model="script.content" rows="14" />

        <div class="rewrite">
          <input v-model="rewriteInstruction" placeholder="改写指令，如：增加反转 / 更口语化" />
          <button :disabled="rewriting || !rewriteInstruction.trim()" @click="rewrite">
            {{ rewriting ? '改写中…' : 'AI 改写' }}
          </button>
        </div>
      </div>

      <aside class="panel">
        <div class="block">
          <h3>三段结构</h3>
          <div class="tabs">
            <button :class="{ active: activeTab === 'opening' }" @click="activeTab = 'opening'">开头</button>
            <button :class="{ active: activeTab === 'conflict' }" @click="activeTab = 'conflict'">冲突</button>
            <button :class="{ active: activeTab === 'ending' }" @click="activeTab = 'ending'">结尾</button>
          </div>
          <p class="segment">{{ script.structure[activeTab] || '（暂未识别）' }}</p>
        </div>

        <div class="block">
          <h3>节奏分段（每 15-20 秒）</h3>
          <ul class="beats">
            <li v-for="(b, i) in script.beats" :key="i">
              <span class="time">{{ b.time }}</span>
              <span class="point">{{ b.point }}</span>
            </li>
          </ul>
        </div>

        <div v-if="script.awkward.length" class="block warn">
          <h3>拗口句提示</h3>
          <ul class="awkward">
            <li v-for="(a, i) in script.awkward" :key="i">
              <p>{{ a.sentence }}</p>
              <span v-for="(issue, j) in a.issues" :key="j" class="tag">{{ issue }}</span>
            </li>
          </ul>
        </div>

        <div v-if="entities" class="block">
          <h3>抽取结果</h3>
          <p class="entities">
            角色：{{ entities.characters.map((c) => c.name).join('、') || '无' }}
          </p>
          <p class="entities">
            场景：{{ entities.scenes.map((s) => s.name).join('、') || '无' }}
          </p>
        </div>
      </aside>
    </div>

    <div v-else class="empty">
      <template v-if="isNewProject">
        <p class="hint-title">第一步：创作剧本</p>
        <p>填写上方题材后点击「生成剧本」，AI 将为您生成完整剧本内容。</p>
        <p class="hint-nav">生成后可继续前往「分镜」「定妆」「生图」等后续步骤</p>
      </template>
      <template v-else>
        <p>输入题材后点击「生成剧本」，或保存已有剧本内容。</p>
      </template>
    </div>
  </section>
</template>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.generate-form {
  display: flex;
  gap: 8px;
  flex: 1;
}

.generate-form input {
  flex: 1;
  padding: 9px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
}

.actions {
  display: flex;
  gap: 8px;
}

button {
  padding: 9px 20px;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

button.ghost {
  background: #fff;
  color: #2563eb;
  border: 1px solid #2563eb;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error {
  background: #fef2f2;
  color: #b91c1c;
  padding: 10px 14px;
  border-radius: 8px;
  margin-bottom: 12px;
  font-size: 14px;
}

.notice {
  background: #f0fdf4;
  color: #166534;
  padding: 10px 14px;
  border-radius: 8px;
  margin-bottom: 12px;
  font-size: 14px;
}

.layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 16px;
}

.editor,
.panel .block {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}

.editor h3 {
  font-size: 14px;
  margin-bottom: 10px;
}

.editor textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.7;
  resize: vertical;
}

.rewrite {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.rewrite input {
  flex: 1;
  padding: 9px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
}

.panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.block h3 {
  font-size: 13px;
  color: #475569;
  margin-bottom: 10px;
}

.tabs {
  display: flex;
  gap: 6px;
  margin-bottom: 10px;
}

.tabs button {
  padding: 5px 12px;
  font-size: 12px;
  background: #f1f5f9;
  color: #475569;
}

.tabs button.active {
  background: #2563eb;
  color: #fff;
}

.segment {
  font-size: 13px;
  line-height: 1.7;
  color: #334155;
}

.beats {
  list-style: none;
}

.beats li {
  display: flex;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px dashed #e2e8f0;
  font-size: 13px;
}

.beats .time {
  color: #2563eb;
  font-weight: 600;
  flex-shrink: 0;
}

.warn {
  border: 1px solid #fde68a;
}

.awkward {
  list-style: none;
}

.awkward li {
  padding: 8px 0;
  border-bottom: 1px dashed #e2e8f0;
  font-size: 13px;
}

.awkward .tag {
  display: inline-block;
  background: #fef3c7;
  color: #92400e;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  margin-top: 6px;
}

.entities {
  font-size: 13px;
  color: #334155;
  margin-bottom: 6px;
}

.empty {
  background: #fff;
  border: 1px dashed #cbd5e1;
  border-radius: 12px;
  padding: 48px;
  text-align: center;
  color: #94a3b8;
  font-size: 14px;
}

.hint-title {
  font-size: 18px;
  font-weight: 600;
  color: #334155;
  margin-bottom: 12px;
}

.hint-nav {
  margin-top: 16px;
  color: #2563eb;
  font-size: 13px;
}

/* 项目信息栏 */
.project-header {
  background: #fff;
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.project-title {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.project-genre {
  font-size: 14px;
  color: #64748b;
  padding: 4px 12px;
  background: #f1f5f9;
  border-radius: 20px;
}

.project-status {
  font-size: 13px;
  color: #2563eb;
  margin-left: auto;
}
</style>
