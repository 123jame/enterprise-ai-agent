<script setup lang="ts">
defineProps<{
  value: number
  label?: string
}>()
</script>

<template>
  <div class="progress-wrap">
    <div class="label-row">
      <span>{{ label || 'Progress' }}</span>
      <span>{{ Math.round(value * 100) }}%</span>
    </div>
    <el-progress :percentage="Math.round(value * 100)" :stroke-width="10" />
  </div>
</template>

<style scoped>
.progress-wrap {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.label-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #cbd5e1;
}
</style>
