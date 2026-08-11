<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { request } from '../api/client'

interface Character {
  id: number
  project_id: number
  name: string
  keywords: string
  portrait_path: string | null
  portrait_style: string | null
  created_at: string
  generating?: boolean
}

interface Scene {
  id: number
  project_id: number
  name: string
  desc_words: string
  created_at: string
}

const route = useRoute()
const projectId = Number(route.params.id)

const characters = ref<Character[]>([])
const scenes = ref<Scene[]>([])
const generating = ref<number | null>(null)
const errorMsg = ref('')
const notice = ref('')
const uniformStyle = ref<string | null>(null)

// 新增角色表单
const newCharName = ref('')
const newCharKeywords = ref('')
const newCharStyle = ref('manga')
const portraitStyles = [
  { value: 'manga', label: '卡通' },
  { value: 'realistic', label: '写实' },
  { value: 'chibi', label: 'Q版' },
  { value: 'anime', label: '日系动漫' },
  { value: 'comic', label: '美式漫画' },
  { value: 'watercolor', label: '水彩' },
  { value: 'sketch', label: '素描' },
  { value: 'pixel', label: '像素风' },
  { value: '3d', label: '3D渲染' },
  { value: 'lineart', label: '线稿' },
  { value: 'pop', label: '波普艺术' },
  { value: 'ink', label: '水墨风' },
]

// 新增场景表单
const newSceneName = ref('')
const newSceneDesc = ref('')

async function loadCast() {
  try {
    const [chars, scns] = await Promise.all([
      request<Character[]>('/projects/' + projectId + '/cast/characters'),
      request<Scene[]>('/projects/' + projectId + '/cast/scenes'),
    ])
    characters.value = chars
    scenes.value = scns
  } catch (e) {
    errorMsg.value = (e as Error).message
  }
}

async function addCharacter() {
  if (!newCharName.value.trim() || !newCharKeywords.value.trim()) {
    errorMsg.value = '请填写角色名称和形象关键词'
    return
  }
  errorMsg.value = ''
  try {
    const char = await request<Character>('/projects/' + projectId + '/cast/characters', {
      method: 'POST',
      body: JSON.stringify({
        name: newCharName.value,
        keywords: newCharKeywords.value,
        portrait_style: newCharStyle.value,
      }),
    })
    characters.value.push(char)
    newCharName.value = ''
    newCharKeywords.value = ''
    notice.value = '角色添加成功'
  } catch (e) {
    errorMsg.value = (e as Error).message
  }
}

async function generatePortrait(characterId: number, style?: string) {
  // 不再互斥，每个按钮独立状态
  const char = characters.value.find((c) => c.id === characterId)
  if (!char) return
  char.generating = true
  errorMsg.value = ''
  notice.value = ''
  try {
    const result = await request<any>(
      '/projects/' + projectId + '/cast/characters/' + characterId + '/generate-portrait',
      { method: 'POST', body: JSON.stringify({ portrait_style: style || char.portrait_style }) },
    )
    if (result.data) {
      char.portrait_path = result.data.portrait_path
      if (result.data.portrait_style) char.portrait_style = result.data.portrait_style
    }
    notice.value = '定妆照生成成功'
  } catch (e) {
    errorMsg.value = (e as Error).message
  } finally {
    char.generating = false
  }
}

async function deleteCharacter(characterId: number) {
  if (!confirm('确认删除该角色？')) return
  try {
    await request('/projects/' + projectId + '/cast/characters/' + characterId, {
      method: 'DELETE',
    })
    characters.value = characters.value.filter((c) => c.id !== characterId)
    notice.value = '已删除'
  } catch (e) {
    errorMsg.value = (e as Error).message
  }
}

async function addScene() {
  if (!newSceneName.value.trim() || !newSceneDesc.value.trim()) {
    errorMsg.value = '请填写场景名称和描述词'
    return
  }
  errorMsg.value = ''
  try {
    const scene = await request<Scene>('/projects/' + projectId + '/cast/scenes', {
      method: 'POST',
      body: JSON.stringify({
        name: newSceneName.value,
        desc_words: newSceneDesc.value,
      }),
    })
    scenes.value.push(scene)
    newSceneName.value = ''
    newSceneDesc.value = ''
    notice.value = '场景添加成功'
  } catch (e) {
    errorMsg.value = (e as Error).message
  }
}

async function deleteScene(sceneId: number) {
  if (!confirm('确认删除该场景？')) return
  try {
    await request('/projects/' + projectId + '/cast/scenes/' + sceneId, {
      method: 'DELETE',
    })
    scenes.value = scenes.value.filter((s) => s.id !== sceneId)
    notice.value = '已删除'
  } catch (e) {
    errorMsg.value = (e as Error).message
  }
}

onMounted(loadCast)

async function generateAllPortraits(style: string) {
  notice.value = ''
  errorMsg.value = ''
  for (const char of characters.value) {
    await generatePortrait(char.id, style)
  }
  notice.value = `已将 ${characters.value.length} 个角色统一为${getStyleLabel(style)}风格`
  uniformStyle.value = null
}

function getPortraitUrl(path: string): string {
  return `/media/${path}`
}

function getStyleLabel(style: string | null): string {
  const map: Record<string, string> = {
    manga: '卡通',
    realistic: '写实',
    chibi: 'Q版',
    anime: '日系动漫',
    comic: '美式漫画',
    watercolor: '水彩',
    sketch: '素描',
    pixel: '像素风',
    '3d': '3D渲染',
    lineart: '线稿',
    pop: '波普艺术',
    ink: '水墨风',
  }
  return map[style || 'manga'] || '卡通'
}
</script>

<template>
  <section class="casting-page">
    <div class="header">
      <h1>第三步：角色与场景定妆</h1>
      <p class="subtitle">为剧本中的角色生成定妆照，登记场景描述词</p>
    </div>

    <p v-if="errorMsg" class="error">{{ errorMsg }}</p>
    <p v-if="notice" class="notice">{{ notice }}</p>

    <!-- 角色管理 -->
    <div class="card">
      <div class="card-header">
        <h2>角色列表</h2>
        <div v-if="characters.length > 0" class="uniform-style-btns">
          <span class="style-label">一键统一风格：</span>
          <button
            v-for="s in portraitStyles"
            :key="s.value"
            class="style-btn"
            :class="{ active: uniformStyle === s.value }"
            @click="uniformStyle = s.value; generateAllPortraits(s.value)"
          >
            {{ s.label }}
          </button>
        </div>
      </div>
      <div class="add-form">
        <input v-model="newCharName" placeholder="角色名称" class="input" />
        <input v-model="newCharKeywords" placeholder="形象关键词（如：25岁女性，黑色长发，穿着白色婚纱）" class="input" />
        <select v-model="newCharStyle" class="select">
          <option v-for="s in portraitStyles" :key="s.value" :value="s.value">{{ s.label }}</option>
        </select>
        <button @click="addCharacter">添加角色</button>
      </div>
      <div class="character-grid">
        <div v-for="char in characters" :key="char.id" class="character-card">
          <div class="portrait-placeholder" v-if="!char.portrait_path">
            <span>暂无定妆照</span>
          </div>
          <img v-else :src="getPortraitUrl(char.portrait_path)" :alt="char.name" class="portrait" />
          <div class="char-style-selector">
            <select v-model="char.portrait_style" class="style-select">
              <option v-for="s in portraitStyles" :key="s.value" :value="s.value">{{ s.label }}</option>
            </select>
          </div>
          <div class="char-info">
            <h3>{{ char.name }}</h3>
            <p class="keywords">{{ char.keywords }}</p>
          </div>
          <div class="char-actions">
            <button
              class="ghost"
              :disabled="char.generating"
              @click="generatePortrait(char.id)"
            >
              {{ char.generating ? '生成中…' : '生成定妆照' }}
            </button>
            <button class="ghost danger" @click="deleteCharacter(char.id)">删除</button>
          </div>
        </div>
      </div>
      <div v-if="characters.length === 0" class="empty">暂无角色，请添加</div>
    </div>

    <!-- 场景管理 -->
    <div class="card">
      <h2>场景列表</h2>
      <div class="add-form">
        <input v-model="newSceneName" placeholder="场景名称" class="input" />
        <input v-model="newSceneDesc" placeholder="场景描述词（如：昏暗教堂，彩色玻璃窗，红色地毯）" class="input" />
        <button @click="addScene">添加场景</button>
      </div>
      <div class="scene-list">
        <div v-for="scene in scenes" :key="scene.id" class="scene-item">
          <div class="scene-name">{{ scene.name }}</div>
          <div class="scene-desc">{{ scene.desc_words }}</div>
          <button class="ghost danger small" @click="deleteScene(scene.id)">删除</button>
        </div>
      </div>
      <div v-if="scenes.length === 0" class="empty">暂无场景，请添加</div>
    </div>
  </section>
</template>

<style scoped>
.casting-page {
  max-width: 1000px;
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

.card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}

.card h2 {
  font-size: 16px;
  margin-bottom: 16px;
}

.add-form {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}

.input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
}

.input:focus {
  outline: none;
  border-color: #3b82f6;
}

button {
  padding: 10px 20px;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.select {
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
  background: #fff;
}

.char-style-tag {
  display: inline-block;
  padding: 4px 10px;
  background: #f1f5f9;
  color: #475569;
  border-radius: 12px;
  font-size: 12px;
  align-self: flex-start;
}

.char-style-selector {
  display: flex;
  justify-content: flex-end;
}

.style-select {
  padding: 4px 8px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 12px;
  background: #f8fafc;
  cursor: pointer;
}

.uniform-style-btns {
  display: flex;
  align-items: center;
  gap: 8px;
}

.style-label {
  font-size: 13px;
  color: #64748b;
}

.style-btn {
  padding: 6px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: #f8fafc;
  color: #475569;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.style-btn:hover {
  background: #e0e7ff;
  border-color: #6366f1;
  color: #4338ca;
}

.style-btn.active {
  background: #6366f1;
  border-color: #6366f1;
  color: #fff;
}
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.character-card {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.portrait-placeholder {
  width: 100%;
  aspect-ratio: 3/4;
  background: #f1f5f9;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  font-size: 13px;
}

.portrait {
  width: 100%;
  aspect-ratio: 3/4;
  object-fit: cover;
  border-radius: 8px;
}

.char-info h3 {
  font-size: 15px;
  margin-bottom: 4px;
}

.keywords {
  font-size: 12px;
  color: #64748b;
  line-height: 1.4;
  flex: 1;
}

.char-actions {
  display: flex;
  gap: 8px;
}

.ghost {
  background: #f1f5f9;
  color: #475569;
  padding: 6px 12px;
  font-size: 12px;
}

.ghost:hover:not(:disabled) {
  background: #e2e8f0;
}

.ghost.danger {
  color: #dc2626;
}

.ghost.danger:hover {
  background: #fef2f2;
}

.ghost.small {
  padding: 4px 8px;
  font-size: 11px;
}

.scene-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.scene-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
}

.scene-name {
  font-weight: 500;
  font-size: 14px;
  min-width: 100px;
}

.scene-desc {
  flex: 1;
  font-size: 13px;
  color: #64748b;
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

.empty {
  color: #94a3b8;
  font-size: 14px;
  text-align: center;
  padding: 24px;
}
</style>
