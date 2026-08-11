<script setup lang="ts">
defineProps<{
  title: string
  description: string
}>()
</script>

<template>
  <section class="placeholder">
    <h1>{{ title }}</h1>
    <p>{{ description }}</p>
  </section>
</template>

<style scoped>
.placeholder {
  background: #fff;
  border: 1px dashed #cbd5e1;
  border-radius: 12px;
  padding: 64px 32px;
  text-align: center;
}

.placeholder h1 {
  font-size: 20px;
  color: #334155;
  margin-bottom: 12px;
}

.placeholder p {
  color: #94a3b8;
  font-size: 14px;
}
</style>
