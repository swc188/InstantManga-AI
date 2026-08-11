<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import StepNav from './components/StepNav.vue'

const route = useRoute()

const stepKeys = ['script', 'storyboard', 'casting', 'gallery', 'audio', 'studio']
const isWorkbench = computed(() =>
  stepKeys.includes(route.name as string),
)
</script>

<template>
  <div class="app-layout" :class="{ 'with-nav': isWorkbench }">
    <header class="topbar">
      <RouterLink to="/projects" class="brand">AI 漫剧制作工作台</RouterLink>
      <div class="topbar-right">
        <RouterLink to="/settings/models" class="settings-link">模型配置</RouterLink>
      </div>
    </header>

    <div v-if="isWorkbench" class="workbench">
      <aside class="sidebar">
        <StepNav :current="route.name as string" />
      </aside>
      <main class="content">
        <RouterView />
      </main>
    </div>
    <main v-else class="content full">
      <RouterView />
    </main>
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
  background: #f8fafc;
  color: #0f172a;
}

a {
  text-decoration: none;
  color: inherit;
}
</style>

<style scoped>
.app-layout {
  min-height: 100vh;
}

.topbar {
  height: 56px;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 10;
}

.brand {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
}

.topbar-right .settings-link {
  font-size: 14px;
  color: #475569;
  padding: 6px 12px;
  border-radius: 6px;
}

.topbar-right .settings-link:hover {
  background: #f1f5f9;
}

.workbench {
  display: flex;
  height: calc(100vh - 56px);
}

.sidebar {
  width: 180px;
  border-right: 1px solid #e2e8f0;
  background: #fff;
  flex-shrink: 0;
}

.content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.content.full {
  min-height: calc(100vh - 56px);
}
</style>
