<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'

import { useDashboardStore } from '@/stores/dashboard'

const route = useRoute()
const router = useRouter()
const store = useDashboardStore()

let unsubscribe: (() => void) | undefined

const menuItems = [
  { path: '/dashboard', label: 'Dashboard' },
  { path: '/workflow', label: 'Workflow' },
  { path: '/agents', label: 'Agents' },
  { path: '/project', label: 'Project' },
  { path: '/git', label: 'Git' },
  { path: '/deployment', label: 'Deployment' },
  { path: '/operations', label: 'Operations' },
  { path: '/knowledge', label: 'Knowledge' },
  { path: '/organization', label: 'Organization' },
  { path: '/settings', label: 'Settings' },
]

onMounted(async () => {
  unsubscribe = store.initRealtime()
  await store.fetchProjects()
  await store.fetchAgents()
})

onUnmounted(() => {
  unsubscribe?.()
})

function navigate(path: string) {
  if (path.includes('workflow') && store.currentProjectId) {
    router.push(`/workflow/${store.currentProjectId}`)
    return
  }

  router.push(path)
}
</script>

<template>
  <el-container class="layout">
    <el-aside width="240px" class="sidebar panel">
      <div class="brand">Enterprise AI</div>
      <el-menu
        :default-active="route.path"
        background-color="transparent"
        text-color="#cbd5e1"
        active-text-color="#60a5fa"
      >
        <el-menu-item
          v-for="item in menuItems"
          :key="item.path"
          :index="item.path"
          @click="navigate(item.path)"
        >
          {{ item.label }}
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header panel">
        <div>
          <strong>Visualization Dashboard</strong>
          <span class="subtitle">P13 · Real-time Software Team Console</span>
        </div>
        <el-tag type="success" effect="dark">Live</el-tag>
      </el-header>

      <el-main class="content">
        <RouterView />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout {
  min-height: 100vh;
}

.sidebar {
  margin: 12px 0 12px 12px;
  padding-top: 12px;
}

.brand {
  font-size: 18px;
  font-weight: 700;
  padding: 8px 16px 16px;
  color: #93c5fd;
}

.header {
  margin: 12px 12px 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.subtitle {
  margin-left: 12px;
  color: #94a3b8;
  font-size: 13px;
}

.content {
  padding: 12px;
}
</style>
