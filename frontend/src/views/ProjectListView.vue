<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '../stores/project'

const store = useProjectStore()
const router = useRouter()

const title = ref('')
const genre = ref('')
const creating = ref(false)

// 删除确认状态
const deletingId = ref<number | null>(null)
const deleteConfirmText = ref('')
const deleteError = ref('')

onMounted(() => {
  store.fetchProjects()
})

async function handleCreate() {
  if (!title.value.trim()) return
  creating.value = true
  try {
    const project = await store.createProject({
      title: title.value.trim(),
      genre: genre.value || undefined,
    })
    // 自动填写题材到 script 页面的输入框，通过路由 query 参数传递
    router.push({
      path: `/projects/${project.id}/script`,
      query: { genre: genre.value || '', fromCreate: 'true' },
    })
  } finally {
    creating.value = false
  }
}

async function handleDelete(projectId: number, _projectTitle: string, e: Event) {
  e.stopPropagation()
  deletingId.value = projectId
  deleteConfirmText.value = ''
  deleteError.value = ''
}

async function confirmDelete() {
  if (deletingId.value === null) return
  const project = store.projects.find(p => p.id === deletingId.value)
  if (!project) return

  // 验证用户输入的标题是否匹配
  if (deleteConfirmText.value.trim() !== project.title) {
    deleteError.value = '请输入正确的项目标题以确认删除'
    return
  }

  try {
    await store.deleteProject(deletingId.value)
    deletingId.value = null
    deleteConfirmText.value = ''
    deleteError.value = ''
  } catch (e) {
    deleteError.value = (e as Error).message
  }
}

function cancelDelete() {
  deletingId.value = null
  deleteConfirmText.value = ''
  deleteError.value = ''
}
</script>

<template>
  <section class="project-list">
    <h1>我的项目</h1>

    <form class="create-card" @submit.prevent="handleCreate">
      <h2>新建漫剧项目</h2>
      <div class="form-row">
        <input v-model="title" placeholder="项目标题（如：霸总逆袭第一话）" required />
        <input v-model="genre" placeholder="题材类型（如：重生 / 霸总 / 逆袭）" />
        <button type="submit" :disabled="creating || !title.trim()">
          {{ creating ? '创建中…' : '创建' }}
        </button>
      </div>
    </form>

    <div class="grid">
      <div
        v-for="p in store.projects"
        :key="p.id"
        class="project-card"
        @click="router.push({ path: `/projects/${p.id}/script`, query: { genre: p.genre || '' } })"
      >
        <div class="card-header">
          <h3>{{ p.title }}</h3>
          <button
            class="delete-btn"
            @click.stop="handleDelete(p.id, p.title, $event)"
            title="删除项目"
          >
            删除
          </button>
        </div>
        <p v-if="p.genre">题材：{{ p.genre }}</p>
        <p class="meta">状态：{{ p.status }}</p>
      </div>
    </div>

    <!-- 删除确认弹窗 -->
    <div v-if="deletingId !== null" class="delete-modal-overlay" @click="cancelDelete">
      <div class="delete-modal" @click.stop>
        <h3>确认删除项目</h3>
        <p class="delete-warning">此操作不可撤销，项目的所有数据将被永久删除。</p>
        <p class="delete-hint">请输入项目标题 "<strong>{{ store.projects.find(p => p.id === deletingId)?.title }}</strong>" 以确认删除</p>
        <input
          v-model="deleteConfirmText"
          type="text"
          placeholder="输入项目标题确认删除"
          class="delete-confirm-input"
          @keyup.enter="confirmDelete"
        />
        <p v-if="deleteError" class="delete-error">{{ deleteError }}</p>
        <div class="delete-actions">
          <button class="ghost" @click="cancelDelete">取消</button>
          <button class="danger" :disabled="deleteConfirmText.trim() !== store.projects.find(p => p.id === deletingId)?.title" @click="confirmDelete">确认删除</button>
        </div>
      </div>
    </div>

    <p v-if="store.loading" class="hint">加载中…</p>
    <p v-else-if="store.projects.length === 0" class="hint">
      暂无项目，先在上方创建第一个项目开始创作
    </p>
  </section>
</template>

<style scoped>
.project-list h1 {
  font-size: 22px;
  margin-bottom: 20px;
}

.create-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}

.create-card h2 {
  font-size: 15px;
  margin-bottom: 14px;
}

.form-row {
  display: flex;
  gap: 12px;
}

.form-row input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
}

.form-row button {
  padding: 10px 24px;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.form-row button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.project-card {
  background: #fff;
  border-radius: 12px;
  padding: 18px;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
  transition: transform 0.15s;
}

.project-card:hover {
  transform: translateY(-2px);
}

.project-card h3 {
  font-size: 15px;
  margin-bottom: 6px;
}

.project-card p {
  font-size: 13px;
  color: #64748b;
}

.meta {
  margin-top: 8px;
}

.hint {
  color: #94a3b8;
  font-size: 14px;
  text-align: center;
  padding: 32px 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.delete-btn {
  padding: 4px 10px;
  font-size: 12px;
  background: #fee2e2;
  color: #dc2626;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  flex-shrink: 0;
  margin-left: 8px;
}

.delete-btn:hover {
  background: #fecaca;
}

/* 删除确认弹窗 */
.delete-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.delete-modal {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  width: 90%;
  max-width: 420px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.delete-modal h3 {
  font-size: 18px;
  color: #dc2626;
  margin-bottom: 12px;
}

.delete-warning {
  color: #dc2626;
  font-size: 14px;
  margin-bottom: 12px;
}

.delete-hint {
  font-size: 14px;
  color: #475569;
  margin-bottom: 12px;
  line-height: 1.5;
}

.delete-confirm-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
  margin-bottom: 12px;
}

.delete-confirm-input:focus {
  outline: none;
  border-color: #2563eb;
}

.delete-error {
  color: #dc2626;
  font-size: 13px;
  margin-bottom: 12px;
}

.delete-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.delete-actions button {
  padding: 8px 20px;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  border: none;
}

.delete-actions .ghost {
  background: #f1f5f9;
  color: #475569;
}

.delete-actions .ghost:hover {
  background: #e2e8f0;
}

.delete-actions .danger {
  background: #dc2626;
  color: #fff;
}

.delete-actions .danger:hover:not(:disabled) {
  background: #b91c1c;
}

.delete-actions .danger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
