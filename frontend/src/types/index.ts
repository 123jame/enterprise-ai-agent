export interface ProjectSummary {
  id: string
  session_id?: string
  name: string
  requirement: string
  status: string
  current_stage?: string
  started_at?: string
  finished_at?: string
  workspace_path?: string
}

export interface WorkflowStage {
  id: string
  label: string
  status: string
  started_at?: string
  finished_at?: string
  detail?: string
}

export interface AgentState {
  name: string
  status: string
  current_task?: string
  token_usage?: number
  execution_time_ms?: number
  tool_calls?: number
  workload?: number
}

export interface DashboardEvent {
  type: string
  project_id?: string
  session_id?: string
  payload?: Record<string, unknown>
  timestamp?: string
}

export interface CreateProjectPayload {
  requirement: string
  project_name?: string
  user_id?: string
}
