<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import MetricCard from '@/components/MetricCard.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import api from '@/services/api'
import { useDashboardStore } from '@/stores/dashboard'

const route = useRoute()
const store = useDashboardStore()
const data = ref<any>(null)

const projectId = computed(
  () => String(route.params.projectId || store.currentProjectId || ''),
)

async function load() {
  if (!projectId.value) return
  const response = await api.getDeployment(projectId.value)
  data.value = response.data
}

onMounted(load)
watch(projectId, load)
</script>

<template>
  <div>
    <h1 class="page-title">Deployment</h1>

    <div v-if="data" class="grid-3">
      <MetricCard
        title="Build"
        :value="data.build?.success ? 'Success' : 'Pending'"
      />
      <MetricCard title="Package" :value="data.package?.version || 'n/a'" />
      <MetricCard title="Deploy URL" :value="data.deploy?.url || 'n/a'" />

      <section class="panel">
        <h3>Build</h3>
        <StatusBadge :status="data.build?.success ? 'completed' : 'pending'" />
        <p>{{ data.build?.detail || 'Waiting for build' }}</p>
      </section>

      <section class="panel">
        <h3>Health Check</h3>
        <StatusBadge
          :status="data.health_check?.success ? 'healthy' : 'pending'"
        />
      </section>

      <section class="panel">
        <h3>Release</h3>
        <p>Version: {{ data.release?.version || 'n/a' }}</p>
        <p>URL: {{ data.release?.url || 'n/a' }}</p>
      </section>
    </div>

    <el-empty v-else description="暂无部署数据" />
  </div>
</template>
