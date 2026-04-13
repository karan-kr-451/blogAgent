import axios from 'axios'

const API_BASE = 'http://localhost:8000'

export interface BlogPost {
  id: string
  title: string
  content: string
  tags: string[]
  word_count: number
  source_url: string
  generated_at: string
  file_path: string
}

export interface PipelineStatus {
  status: string
  current_step: string
  items_processed: number
  errors: string[]
  last_run: string | null
}

export interface SystemStats {
  total_processed: number
  duplicates_detected: number
  last_publication: string | null
  success_rate: number
}

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
})

export const getBlogPosts = async (): Promise<BlogPost[]> => {
  // For now, we'll parse the drafts directory
  // In production, you'd have an endpoint to list drafts
  const response = await api.get('/history')
  return response.data
}

export const getPipelineStatus = async (): Promise<PipelineStatus> => {
  const response = await api.get('/pipeline/status')
  return response.data
}

export const getStats = async (): Promise<SystemStats> => {
  const response = await api.get('/stats')
  return response.data
}

export const triggerPipeline = async (): Promise<any> => {
  const response = await api.post('/pipeline/trigger')
  return response.data
}

export default api
