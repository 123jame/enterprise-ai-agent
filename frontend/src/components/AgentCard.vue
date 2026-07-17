<script setup lang="ts">
import StatusBadge from './StatusBadge.vue'

defineProps<{
  name: string
  status: string
  currentTask?: string
  tokenUsage?: number
  executionTimeMs?: number
  toolCalls?: number
  workload?: number
}>()
</script>

<template>
  <div class="agent-card panel">
    <div class="header">
      <strong>{{ name }}</strong>
      <StatusBadge :status="status" />
    </div>
    <p class="task">{{ currentTask || 'Waiting for assignment' }}</p>
    <div class="metrics">
      <span>Tokens: {{ tokenUsage ?? 0 }}</span>
      <span>Time: {{ ((executionTimeMs ?? 0) / 1000).toFixed(1) }}s</span>
      <span>Tools: {{ toolCalls ?? 0 }}</span>
      <span>Load: {{ (workload ?? 0).toFixed(0) }}%</span>
    </div>
  </div>
</template>

<style scoped>
.agent-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task {
  margin: 0;
  color: #94a3b8;
  font-size: 13px;
}

.metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
  font-size: 12px;
  color: #cbd5e1;
}
</style>
