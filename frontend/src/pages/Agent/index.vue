<script setup lang="ts">
import { onMounted } from 'vue'

import AgentCard from '@/components/AgentCard.vue'
import { useDashboardStore } from '@/stores/dashboard'

const store = useDashboardStore()

onMounted(() => {
  store.fetchAgents(store.currentProjectId)
})
</script>

<template>
  <div>
    <h1 class="page-title">Agents</h1>

    <div class="grid-3">
      <AgentCard
        v-for="agent in store.agents"
        :key="agent.name"
        :name="agent.name"
        :status="agent.status"
        :current-task="agent.current_task"
        :token-usage="agent.token_usage"
        :execution-time-ms="agent.execution_time_ms"
        :tool-calls="agent.tool_calls"
        :workload="agent.workload"
      />
    </div>
  </div>
</template>
