<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import MetricCard from '@/components/MetricCard.vue'
import Timeline from '@/components/Timeline.vue'
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
  const response = await api.getOperations(projectId.value)
  data.value = response.data
}

onMounted(load)
watch(projectId, load)
</script>

<template>
  <div>
    <h1 class="page-title">Operations</h1>

    <div v-if="data" class="grid-2">
      <MetricCard title="CPU" :value="`${data.cpu?.value ?? 0}${data.cpu?.unit || '%'}`" />
      <MetricCard
        title="Memory"
        :value="`${data.memory?.value ?? 0}${data.memory?.unit || 'MB'}`"
      />

      <section class="panel">
        <h3>Service Health</h3>
        <p>Status: {{ data.health?.status || 'unknown' }}</p>
        <el-table :data="data.services || []" size="small">
          <el-table-column prop="name" label="Service" />
          <el-table-column prop="status" label="Status" />
        </el-table>
      </section>

      <section class="panel">
        <h3>Alerts</h3>
        <Timeline
          :items="
            (data.alerts || []).map((item: any, index: number) => ({
              id: `${item.id || index}`,
              title: item.title || item.message || 'Alert',
              status: item.severity || 'warning',
            }))
          "
        />
      </section>

      <section class="panel" style="grid-column: 1 / -1">
        <h3>Incidents</h3>
        <Timeline
          :items="
            (data.incidents || []).map((item: any, index: number) => ({
              id: `${item.id || index}`,
              title: item.title || item.id || 'Incident',
              subtitle: item.summary,
              status: item.status || 'open',
            }))
          "
        />
      </section>
    </div>

    <el-empty v-else description="暂无运维数据" />
  </div>
</template>
