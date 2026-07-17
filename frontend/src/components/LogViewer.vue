<script setup lang="ts">
defineProps<{
  logs: string[]
}>()
</script>

<template>
  <div class="log-viewer panel">
    <div v-if="!logs.length" class="empty">No logs yet</div>
    <div v-for="(line, index) in logs" :key="index" class="line">
      {{ line }}
    </div>
  </div>
</template>

<style scoped>
.log-viewer {
  max-height: 320px;
  overflow: auto;
  font-family: Consolas, monospace;
  font-size: 12px;
  line-height: 1.6;
}

.line {
  padding: 2px 0;
  color: #cbd5e1;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.empty {
  color: #64748b;
}
</style>
