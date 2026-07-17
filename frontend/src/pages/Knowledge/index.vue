<script setup lang="ts">
import { onMounted, ref } from 'vue'

import ProjectTree from '@/components/ProjectTree.vue'
import api from '@/services/api'
import { useDashboardStore } from '@/stores/dashboard'

const store = useDashboardStore()
const data = ref<any>(null)

onMounted(async () => {
  const response = await api.getKnowledge(store.currentProjectId)
  data.value = response.data
})
</script>

<template>
  <div>
    <h1 class="page-title">Knowledge</h1>

    <div v-if="data" class="grid-2">
      <section class="panel">
        <h3>Knowledge Base</h3>
        <el-table :data="data.knowledge_base || []" size="small">
          <el-table-column prop="title" label="Title" />
          <el-table-column prop="category" label="Category" width="140" />
        </el-table>
      </section>

      <section class="panel">
        <h3>Knowledge Tree</h3>
        <ProjectTree
          :nodes="
            (data.knowledge_base || []).map((item: any) => ({
              id: item.id,
              label: item.title,
            }))
          "
        />
      </section>

      <section class="panel">
        <h3>Best Practices</h3>
        <ul>
          <li v-for="(item, index) in data.best_practices || []" :key="index">
            {{ item }}
          </li>
        </ul>
      </section>

      <section class="panel">
        <h3>Lessons Learned</h3>
        <ul>
          <li v-for="(item, index) in data.lessons_learned || []" :key="index">
            {{ item }}
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>
