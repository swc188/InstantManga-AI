<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { request } from '../api/client'

interface Storyboard {
  id: number
  project_id: number
  shot_no: number
  scene_desc: string
  shot_type: string
  camera_angle: string | null
  dialogue: string | null
  emotion: string | null
  duration: number
  created_at: string
}

interface Validation {
  uncovered_dialogues: string[]
  transition_issues: Array<{
    from_shot: number
    to_shot: number
    reason: string
  }>
}

interface StoryboardData {
  storyboards: Storyboard[]
  validation: Validation
}

const route = useRoute()
const projectId = Number(route.params.id)

const storyboards = ref<Storyboard[]>([])
const validation = ref<Validation>({ uncovered_dialogues: [], transition_issues: [] })
const generating = ref(false)
const saving = ref(false)
const errorMsg = ref('')
const notice = ref('')
const scriptContent = ref('')

async function generate() {
  if (!scriptContent.value.trim()) {
    errorMsg.value = '请先输入剧本内容'
    return
  }
  generating.value = true
  errorMsg.value = ''
  notice.value = ''
  try {
    const data = await request<StoryboardData>(`/projects/${projectId}/storyboard/generate`, {
      method: 'POST',
      body: JSON.stringify({ content: scriptContent.value }),
    })
    storyboards.value = data.storyboards
    validation.value = data.validation
    notice.value = `已生成 ${data.storyboards.length} 个镜头`
  } catch (e) {
    errorMsg.value = (e as Error).message
  } finally {
    generating.value = false
  }
}

async function updateShot(shot: Storyboard) {
  saving.value = true
  errorMsg.value = ''
  try {
    await request(`/projects/${projectId}/storyboard`, {
      method: 'PUT',
      body: JSON.stringify(shot),
    })
    notice.value = '已保存'
  } catch (e) {
    errorMsg.value = (e as Error).message
  } finally {
    saving.value = false
  }
}

async function loadStoryboards() {
  try {
    const data = await request<Storyboard[]>(`/projects/${projectId}/storyboard`)
    storyboards.value = data
  } catch {
    storyboards.value = []
  }
  // 尝试加载已有剧本内容
  try {
    const script = await request<{ content: string }>(`/projects/${projectId}/script`)
    scriptContent.value = script.content
  } catch {
    scriptContent.value = ''
  }
}

function reorderShots(fromIndex: number, toIndex: number) {
  const [removed] = storyboards.value.splice(fromIndex, 1)
  storyboards.value.splice(toIndex, 0, removed)
  // 重新编号
  storyboards.value.forEach((sb, i) => {
    sb.shot_no = i + 1
  })
}

onMounted(loadStoryboards)
</script>

<template>
  <section class="storyboard-page">
    <div class="header">
      <h1>第二步：写分镜</h1>
      <p class="subtitle">将剧本拆解为 20-30 张图的画面清单</p>
    </div>

    <div class="input-section">
      <h3>剧本内容</h3>
      <textarea
        v-model="scriptContent"
        placeholder="粘贴或输入剧本内容，点击「生成分镜」自动拆解"
        rows="6"
      />
      <button :disabled="generating || !scriptContent.trim()" @click="generate">
        {{ generating ? '生成中…' : '生成分镜' }}
      </button>
    </div>

    <p v-if="errorMsg" class="error">{{ errorMsg }}</p>
    <p v-if="notice" class="notice">{{ notice }}</p>

    <!-- 校验提示 -->
    <div v-if="validation.uncovered_dialogues.length" class="warning-box">
      <h4>台词覆盖检查</h4>
      <p>以下台词未分配到分镜：</p>
      <ul>
        <li v-for="(d, i) in validation.uncovered_dialogues" :key="i">{{ d }}</li>
      </ul>
    </div>

    <div v-if="validation.transition_issues.length" class="warning-box">
      <h4>过渡检查</h4>
      <ul>
        <li v-for="(issue, i) in validation.transition_issues" :key="i">
          镜头 {{ issue.from_shot }} → {{ issue.to_shot }}：{{ issue.reason }}
        </li>
      </ul>
    </div>

    <!-- 分镜表 -->
    <div v-if="storyboards.length" class="storyboard-table">
      <h3>分镜列表（{{ storyboards.length }} 个镜头）</h3>
      <table>
        <thead>
          <tr>
            <th>镜头号</th>
            <th>画面描述</th>
            <th>景别</th>
            <th>角度</th>
            <th>台词</th>
            <th>情绪</th>
            <th>时长</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(shot, index) in storyboards" :key="shot.id">
            <td>{{ shot.shot_no }}</td>
            <td>
              <textarea
                v-model="shot.scene_desc"
                rows="2"
                @blur="updateShot(shot)"
              />
            </td>
            <td>
              <select v-model="shot.shot_type" @change="updateShot(shot)">
                <option value="特写">特写</option>
                <option value="近景">近景</option>
                <option value="中景">中景</option>
                <option value="远景">远景</option>
                <option value="全景">全景</option>
              </select>
            </td>
            <td>
              <select v-model="shot.camera_angle" @change="updateShot(shot)">
                <option value="">-</option>
                <option value="平视">平视</option>
                <option value="俯拍">俯拍</option>
                <option value="仰拍">仰拍</option>
                <option value="侧拍">侧拍</option>
                <option value="主观">主观</option>
              </select>
            </td>
            <td>
              <input
                v-model="shot.dialogue"
                placeholder="台词（可选）"
                @blur="updateShot(shot)"
              />
            </td>
            <td>
              <select v-model="shot.emotion" @change="updateShot(shot)">
                <option value="">-</option>
                <option value="平静">平静</option>
                <option value="紧张">紧张</option>
                <option value="愤怒">愤怒</option>
                <option value="惊讶">惊讶</option>
                <option value="悲伤">悲伤</option>
                <option value="喜悦">喜悦</option>
                <option value="恐惧">恐惧</option>
                <option value="期待">期待</option>
              </select>
            </td>
            <td>
              <input
                type="number"
                v-model.number="shot.duration"
                min="0.5"
                max="5"
                step="0.5"
                @blur="updateShot(shot)"
              />
            </td>
            <td>
              <button class="ghost" @click="reorderShots(index, index - 1)" :disabled="index === 0">↑</button>
              <button class="ghost" @click="reorderShots(index, index + 1)" :disabled="index === storyboards.length - 1">↓</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else class="empty">
      <p>输入剧本内容后点击「生成分镜」，AI 将为您拆解 20-30 个镜头。</p>
      <p class="hint">每个镜头包含画面描述、景别、拍摄角度、台词和情绪标签</p>
    </div>
  </section>
</template>

<style scoped>
.storyboard-page {
  max-width: 1200px;
}

.header {
  margin-bottom: 24px;
}

.header h1 {
  font-size: 22px;
  margin-bottom: 8px;
}

.subtitle {
  color: #64748b;
  font-size: 14px;
}

.input-section {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}

.input-section h3 {
  font-size: 15px;
  margin-bottom: 12px;
}

.input-section textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
  resize: vertical;
  margin-bottom: 12px;
}

.input-section button {
  padding: 10px 24px;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.input-section button:disabled {
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

.warning-box {
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
}

.warning-box h4 {
  font-size: 14px;
  color: #92400e;
  margin-bottom: 8px;
}

.warning-box ul {
  margin: 0;
  padding-left: 20px;
  font-size: 13px;
  color: #78350f;
}

.warning-box li {
  margin-bottom: 4px;
}

.storyboard-table {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}

.storyboard-table h3 {
  font-size: 15px;
  margin-bottom: 16px;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

th {
  text-align: left;
  padding: 10px 8px;
  border-bottom: 2px solid #e2e8f0;
  color: #475569;
  font-weight: 600;
}

td {
  padding: 8px;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: top;
}

tr:hover {
  background: #f8fafc;
}

td textarea,
td input {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 13px;
}

td select {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 13px;
  background: #fff;
}

td input[type="number"] {
  width: 60px;
}

button.ghost {
  padding: 4px 8px;
  background: #f1f5f9;
  color: #475569;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  margin: 0 2px;
}

button.ghost:hover:not(:disabled) {
  background: #e2e8f0;
}

button.ghost:disabled {
  opacity: 0.3;
  cursor: not-allowed;
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

.empty .hint {
  margin-top: 8px;
  font-size: 13px;
  color: #cbd5e1;
}
</style>
