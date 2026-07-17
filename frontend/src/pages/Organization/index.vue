<script setup lang="ts">
import { onMounted, ref } from 'vue'

import ProjectTree from '@/components/ProjectTree.vue'
import api from '@/services/api'

const data = ref<any>(null)

onMounted(async () => {
  const response = await api.getOrganization()
  data.value = response.data
})
</script>

<template>
  <div>
    <h1 class="page-title">Organization</h1>

    <div v-if="data" class="grid-2">
      <section class="panel">
        <h3>Organization</h3>
        <p>{{ data.organization_summary }}</p>
      </section>

      <section class="panel">
        <h3>Permissions</h3>
        <pre>{{ data.permissions }}</pre>
      </section>

      <section class="panel">
        <h3>Workspaces</h3>
        <el-table :data="data.workspaces || []" size="small">
          <el-table-column prop="name" label="Name" />
          <el-table-column prop="root_path" label="Path" />
        </el-table>
      </section>

      <section class="panel">
        <h3>Teams</h3>
        <el-table :data="data.teams || []" size="small">
          <el-table-column prop="name" label="Name" />
          <el-table-column prop="team_type" label="Type" width="140" />
        </el-table>
      </section>

      <section class="panel" style="grid-column: 1 / -1">
        <h3>Projects</h3>
        <ProjectTree
          :nodes="
            (data.projects || []).map((item: any) => ({
              id: item.id,
              label: `${item.name} (${item.status})`,
            }))
          "
        />
      </section>
    </div>
  </div>
</template>

<style scoped>
pre {
  white-space: pre-wrap;
  color: #cbd5e1;
}
</style>
