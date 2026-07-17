<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'

import LogViewer from '@/components/LogViewer.vue'
import WorkflowView from '@/components/WorkflowView.vue'
import { useDashboardStore } from '@/stores/dashboard'

const route = useRoute()
const store = useDashboardStore()

const projectId = computed(
  () => String(route.params.projectId || store.currentProjectId || ''),
)

const stages = computed(() => {
  if (store.workflowStages.length) return store.workflowStages

  return [
    'Requirement',
    'Planning',
    'Architecture',
    'Development',
    'Verification',
    'Git',
    'Deployment',
    'Operations',
    'Knowledge',
    'Completed',
  ].map((label) => ({
    id: label.toLowerCase(),
    label,
    status: 'pending',
  }))
})

async function load() {
  if (!projectId.value) return
  await store.fetchWorkflow(projectId.value)
}

onMounted(load)
watch(projectId, load)
</script>

<template>
  <div>
    <h1 class="page-title">Workflow</h1>

    <div class="grid-2">
      <section class="panel">
        <h3>实时流水线</h3>
        <WorkflowView :stages="stages" />
      </section>

      <section class="panel">
        <h3>运行日志</h3>
        <LogViewer :logs="store.logs" />
      </section>
    </div>
  </div>
</template>
