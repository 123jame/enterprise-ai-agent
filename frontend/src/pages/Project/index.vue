<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import LogViewer from '@/components/LogViewer.vue'
import ProgressBar from '@/components/ProgressBar.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import Timeline from '@/components/Timeline.vue'
import api from '@/services/api'
import { useDashboardStore } from '@/stores/dashboard'

const route = useRoute()
const store = useDashboardStore()
const detail = ref<any>(null)

const projectId = computed(
  () => String(route.params.projectId || store.currentProjectId || ''),
)

async function load() {
  if (!projectId.value) return
  const { data } = await api.getProjectDetail(projectId.value)
  detail.value = data
}

onMounted(load)
watch(projectId, load)
</script>

<template>
  <div>
    <h1 class="page-title">Project</h1>

    <div v-if="detail" class="grid-2">
      <section class="panel">
        <h3>{{ detail.project.name }}</h3>
        <p>{{ detail.project.requirement }}</p>
        <StatusBadge :status="detail.project.status" />
        <ProgressBar
          :value="detail.progress.completion_rate || 0"
          label="项目进度"
        />
      </section>

      <section class="panel">
        <h3>Milestones</h3>
        <Timeline
          :items="
            detail.milestones.map((item: any) => ({
              id: item.id,
              title: item.name,
              status: item.status,
            }))
          "
        />
      </section>

      <section class="panel">
        <h3>Tasks</h3>
        <el-table :data="detail.tasks" size="small">
          <el-table-column prop="title" label="任务" />
          <el-table-column prop="assignee" label="负责人" width="140" />
          <el-table-column label="状态" width="120">
            <template #default="{ row }">
              <StatusBadge :status="row.status" />
            </template>
          </el-table-column>
        </el-table>
      </section>

      <section class="panel">
        <h3>Risks</h3>
        <Timeline
          :items="
            detail.risks.map((item: any) => ({
              id: item.id,
              title: item.title,
              subtitle: item.description,
              status: item.level,
            }))
          "
        />
      </section>

      <section class="panel" style="grid-column: 1 / -1">
        <h3>Logs</h3>
        <LogViewer :logs="detail.logs" />
      </section>
    </div>

    <el-empty v-else description="请选择一个项目" />
  </div>
</template>
