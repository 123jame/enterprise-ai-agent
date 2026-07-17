<script setup lang="ts">
import StatusBadge from './StatusBadge.vue'

defineProps<{
  items: Array<{
    id: string
    title: string
    subtitle?: string
    status?: string
    timestamp?: string
  }>
}>()
</script>

<template>
  <div class="timeline">
    <div v-for="item in items" :key="item.id" class="timeline-item">
      <div class="dot" />
      <div class="content">
        <div class="row">
          <strong>{{ item.title }}</strong>
          <StatusBadge v-if="item.status" :status="item.status" />
        </div>
        <p v-if="item.subtitle">{{ item.subtitle }}</p>
        <small v-if="item.timestamp">{{ item.timestamp }}</small>
      </div>
    </div>
  </div>
</template>

<style scoped>
.timeline {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.timeline-item {
  display: flex;
  gap: 12px;
}

.dot {
  width: 10px;
  height: 10px;
  margin-top: 6px;
  border-radius: 50%;
  background: #60a5fa;
}

.content {
  flex: 1;
}

.row {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

p,
small {
  margin: 4px 0 0;
  color: #94a3b8;
}
</style>
