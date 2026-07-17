<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import MetricCard from '@/components/MetricCard.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { useDashboardStore } from '@/stores/dashboard'

const store = useDashboardStore()
const router = useRouter()

const requirement = ref('开发一个图书管理系统')
const projectName = ref('Library System')
const starting = ref(false)

onMounted(() => {
  store.fetchProjects()
})

async function handleStart() {
  if (!requirement.value.trim()) {
    ElMessage.warning('请输入需求')
    return
  }

  starting.value = true

  try {
    const result = await store.startProject(
      requirement.value.trim(),
      projectName.value.trim() || undefined,
    )

    ElMessage.success('项目已启动')
    router.push(`/workflow/${result.project_id}`)
  } finally {
    starting.value = false
  }
}

function openProject(projectId: string) {
  store.currentProjectId = projectId
  router.push(`/project/${projectId}`)
}
</script>

<template>
  <div>
    <h1 class="page-title">Dashboard</h1>

    <div class="grid-2">
      <section class="panel">
        <h3>创建项目</h3>
        <el-form label-position="top">
          <el-form-item label="项目名称">
            <el-input v-model="projectName" placeholder="Library System" />
          </el-form-item>
          <el-form-item label="用户需求">
            <el-input
              v-model="requirement"
              type="textarea"
              :rows="4"
              placeholder="描述你要开发的系统..."
            />
          </el-form-item>
          <el-button type="primary" :loading="starting" @click="handleStart">
            启动开发
          </el-button>
        </el-form>
      </section>

      <section class="grid-3" style="grid-template-columns: 1fr">
        <MetricCard title="项目总数" :value="store.projects.length" />
        <MetricCard
          title="运行中"
          :value="store.projects.filter((p) => p.status === 'running').length"
        />
        <MetricCard title="Agent 数量" :value="store.agents.length" />
      </section>
    </div>

    <section class="panel" style="margin-top: 16px">
      <h3>历史项目</h3>
      <el-table :data="store.projects" style="width: 100%">
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="requirement" label="需求" show-overflow-tooltip />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <StatusBadge :status="row.status" />
          </template>
        </el-table-column>
        <el-table-column prop="current_stage" label="阶段" width="140" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button link type="primary" @click="openProject(row.id)">
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>
