<script setup lang="ts">
import { onMounted, ref } from 'vue'

import api from '@/services/api'

const settings = ref<any>(null)

onMounted(async () => {
  const response = await api.getSettings()
  settings.value = response.data
})
</script>

<template>
  <div>
    <h1 class="page-title">Settings</h1>

    <div v-if="settings" class="grid-2">
      <section
        v-for="section in [
          ['LLM', settings.llm],
          ['Memory', settings.memory],
          ['Workflow', settings.workflow],
          ['Git', settings.git],
          ['Deployment', settings.deployment],
          ['Prompt', settings.prompt],
        ]"
        :key="section[0]"
        class="panel"
      >
        <h3>{{ section[0] }}</h3>
        <pre>{{ JSON.stringify(section[1], null, 2) }}</pre>
      </section>

      <section class="panel">
        <h3>Models</h3>
        <el-table :data="settings.model?.models || []" size="small">
          <el-table-column prop="name" label="Name" />
          <el-table-column prop="provider" label="Provider" width="140" />
          <el-table-column prop="id" label="ID" />
        </el-table>
      </section>
    </div>
  </div>
</template>

<style scoped>
pre {
  white-space: pre-wrap;
  color: #cbd5e1;
  font-size: 12px;
}
</style>
