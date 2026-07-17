<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

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
  const response = await api.getGit(projectId.value)
  data.value = response.data
}

onMounted(load)
watch(projectId, load)
</script>

<template>
  <div>
    <h1 class="page-title">Git</h1>

    <div v-if="data" class="grid-2">
      <section class="panel">
        <h3>Branches</h3>
        <el-tag v-for="branch in data.branches" :key="branch" style="margin-right: 8px">
          {{ branch }}
        </el-tag>
      </section>

      <section class="panel">
        <h3>Releases</h3>
        <Timeline
          :items="
            (data.releases || []).map((item: any) => ({
              id: item.version,
              title: item.version,
              subtitle: item.url,
            }))
          "
        />
      </section>

      <section class="panel">
        <h3>Commits</h3>
        <Timeline
          :items="
            (data.commits || []).map((item: any, index: number) => ({
              id: `${item.sha || index}`,
              title: item.message || item.sha,
              subtitle: item.branch,
              status: 'completed',
            }))
          "
        />
      </section>

      <section class="panel">
        <h3>Merges</h3>
        <Timeline
          :items="
            (data.merges || []).map((item: any, index: number) => ({
              id: `${item.merge || index}`,
              title: item.merge,
              subtitle: item.agent,
              status: item.success ? 'completed' : 'failed',
            }))
          "
        />
      </section>
    </div>

    <el-empty v-else description="暂无 Git 数据" />
  </div>
</template>
