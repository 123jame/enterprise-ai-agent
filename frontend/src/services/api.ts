import axios from 'axios'
import type { CreateProjectPayload, ProjectSummary } from '@/types'

const client = axios.create({
  baseURL: '/api/v1/dashboard',
  timeout: 30000,
})

export const api = {
  listProjects: () => client.get<ProjectSummary[]>('/projects'),
  createProject: (payload: CreateProjectPayload) =>
    client.post('/projects', payload),
  getProject: (projectId: string) => client.get(`/projects/${projectId}`),
  getProjectDetail: (projectId: string) =>
    client.get(`/projects/${projectId}/detail`),
  getWorkflow: (projectId: string) => client.get(`/workflow/${projectId}`),
  getAgents: (projectId = '') =>
    client.get('/agents', { params: { project_id: projectId } }),
  getGit: (projectId: string) => client.get(`/git/${projectId}`),
  getDeployment: (projectId: string) =>
    client.get(`/deployment/${projectId}`),
  getOperations: (projectId: string) =>
    client.get(`/operations/${projectId}`),
  getKnowledge: (projectId = '') =>
    client.get('/knowledge', { params: { project_id: projectId } }),
  getOrganization: () => client.get('/organization'),
  getSettings: () => client.get('/settings'),
  getMemory: (sessionId: string) => client.get(`/memory/${sessionId}`),
  getPromptDebug: (projectId: string) =>
    client.get(`/prompts/debug/${projectId}`),
}

export default api
