<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '../stores/project'

const store = useProjectStore()
const router = useRouter()

const title = ref('')
const genre = ref('')
const creating = ref(false)

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
    router.push(`/projects/${project.id}/script`)
  } finally {
    creating.value = false
  }
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
        @click="router.push(`/projects/${p.id}/script`)"
      >
        <h3>{{ p.title }}</h3>
        <p v-if="p.genre">题材：{{ p.genre }}</p>
        <p class="meta">状态：{{ p.status }}</p>
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
</style>
