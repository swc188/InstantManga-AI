<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { computed } from 'vue'

const route = useRoute()
const router = useRouter()

const projectId = route.params.id

const steps = [
  { key: 'script', label: '剧本' },
  { key: 'storyboard', label: '分镜' },
  { key: 'casting', label: '定妆' },
  { key: 'gallery', label: '生图' },
  { key: 'audio', label: '音频' },
  { key: 'studio', label: '剪辑' },
]

const currentStep = computed(() => route.name as string)

function navigateTo(key: string) {
  router.push(`/projects/${projectId}/${key}`)
}
</script>

<template>
  <nav class="step-nav">
    <div
      v-for="(step, idx) in steps"
      :key="step.key"
      class="step-item"
      :class="{ active: step.key === currentStep }"
      @click="navigateTo(step.key)"
    >
      <span class="step-index">{{ idx + 1 }}</span>
      <span class="step-label">{{ step.label }}</span>
    </div>
  </nav>
</template>

<style scoped>
.step-nav {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  color: #64748b;
  font-size: 14px;
}

.step-item:hover {
  background: #f1f5f9;
}

.step-item.active {
  background: #2563eb;
  color: #fff;
}

.step-index {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  background: #e2e8f0;
  color: #475569;
}

.step-item.active .step-index {
  background: rgba(255, 255, 255, 0.25);
  color: #fff;
}
</style>
