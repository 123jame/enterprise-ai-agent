import { defineStore } from 'pinia'
import { ref } from 'vue'

import api from '@/services/api'
import dashboardWebSocket from '@/services/websocket'
import type { AgentState, DashboardEvent, ProjectSummary, WorkflowStage } from '@/types'

export const useDashboardStore = defineStore('dashboard', () => {
  const projects = ref<ProjectSummary[]>([])
  const currentProjectId = ref('')
  const workflowStages = ref<WorkflowStage[]>([])
  const agents = ref<AgentState[]>([])
  const logs = ref<string[]>([])
  const loading = ref(false)
  const events = ref<DashboardEvent[]>([])

  async function fetchProjects() {
    loading.value = true

    try {
      const { data } = await api.listProjects()
      projects.value = data
    } finally {
      loading.value = false
    }
  }

  async function startProject(requirement: string, projectName?: string) {
    const { data } = await api.createProject({
      requirement,
      project_name: projectName,
    })

    currentProjectId.value = data.project_id
    await fetchProjects()
    await fetchWorkflow(data.project_id)
    await fetchAgents(data.project_id)

    return data
  }

  async function fetchWorkflow(projectId: string) {
    if (!projectId) return

    const { data } = await api.getWorkflow(projectId)
    workflowStages.value = data.stages || []
    logs.value = data.logs || []
  }

  async function fetchAgents(projectId = '') {
    const { data } = await api.getAgents(projectId)
    agents.value = data
  }

  function handleEvent(event: DashboardEvent) {
    events.value = [...events.value.slice(-99), event]

    if (event.type === 'log' && event.payload?.message) {
      logs.value = [...logs.value.slice(-99), String(event.payload.message)]
    }

    if (event.project_id) {
      currentProjectId.value = event.project_id
    }

    if (
      event.type === 'workflow_status' &&
      event.payload?.stage &&
      event.payload?.status
    ) {
      const stageId = String(event.payload.stage)
      workflowStages.value = workflowStages.value.map((stage) =>
        stage.id === stageId
          ? {
              ...stage,
              status: String(event.payload?.status),
              detail: String(event.payload?.detail || stage.detail || ''),
            }
          : stage,
      )
    }

    if (event.type === 'agent_started' || event.type === 'agent_finished') {
      fetchAgents(currentProjectId.value)
    }

    if (
      event.type === 'project_started' ||
      event.type === 'project_finished'
    ) {
      fetchProjects()
    }
  }

  function initRealtime() {
    dashboardWebSocket.connect()
    return dashboardWebSocket.subscribe(handleEvent)
  }

  return {
    projects,
    currentProjectId,
    workflowStages,
    agents,
    logs,
    loading,
    events,
    fetchProjects,
    startProject,
    fetchWorkflow,
    fetchAgents,
    initRealtime,
  }
})
