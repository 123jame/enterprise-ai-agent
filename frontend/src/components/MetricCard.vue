<script setup lang="ts">
defineProps<{
  title: string
  value: string | number
  hint?: string
}>()
</script>

<template>
  <div class="metric-card panel">
    <div class="title">{{ title }}</div>
    <div class="value">{{ value }}</div>
    <div v-if="hint" class="hint">{{ hint }}</div>
  </div>
</template>

<style scoped>
.metric-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.title {
  color: #94a3b8;
  font-size: 13px;
}

.value {
  font-size: 28px;
  font-weight: 700;
  color: #f8fafc;
}

.hint {
  color: #64748b;
  font-size: 12px;
}
</style>
