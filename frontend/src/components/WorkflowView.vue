<script setup lang="ts">
import StatusBadge from './StatusBadge.vue'
import type { WorkflowStage } from '@/types'

defineProps<{
  stages: WorkflowStage[]
  currentStage?: string
}>()
</script>

<template>
  <div class="workflow-view">
    <div
      v-for="(stage, index) in stages"
      :key="stage.id"
      class="stage-row"
    >
      <div class="node">
        <StatusBadge :status="stage.status" />
        <div>
          <strong>{{ stage.label }}</strong>
          <p>{{ stage.detail || stage.id }}</p>
        </div>
      </div>
      <div v-if="index < stages.length - 1" class="arrow">↓</div>
    </div>
  </div>
</template>

<style scoped>
.workflow-view {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stage-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.node {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
}

.node p {
  margin: 4px 0 0;
  color: #94a3b8;
  font-size: 12px;
}

.arrow {
  text-align: center;
  color: #64748b;
}
</style>
