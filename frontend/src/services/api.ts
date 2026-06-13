import axios, { AxiosError } from 'axios'
import type { AuthTokens, Case, CaseCreate, ChatResponse } from '../types'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Inyectar token en cada request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Refrescar token si expira
api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const { data } = await axios.post<AuthTokens>(
            `${BASE_URL}/api/auth/refresh`,
            null,
            { headers: { Authorization: `Bearer ${refreshToken}` } }
          )
          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)
          if (error.config) {
            error.config.headers.Authorization = `Bearer ${data.access_token}`
            return api(error.config)
          }
        } catch {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

// ─── Auth ────────────────────────────────────────────────────────────────────

export const authApi = {
  login: (username: string, password: string) =>
    api.post<AuthTokens>('/api/auth/login', new URLSearchParams({ username, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }),

  register: (data: { username: string; email: string; password: string; role?: string }) =>
    api.post<AuthTokens>('/api/auth/register', null, { params: data }),

  me: () => api.get('/api/auth/me'),
}

// ─── Cases ───────────────────────────────────────────────────────────────────

export const casesApi = {
  list: (params?: { status?: string; area?: string; cliente?: string }) =>
    api.get<Case[]>('/api/cases/', { params }),

  get: (id: number) => api.get<Case>(`/api/cases/${id}`),

  create: (data: CaseCreate) => api.post<Case>('/api/cases/', data),

  update: (id: number, data: Partial<CaseCreate>) => api.put<Case>(`/api/cases/${id}`, data),

  delete: (id: number) => api.delete(`/api/cases/${id}`),
}

// ─── Chat REST ───────────────────────────────────────────────────────────────

export const chatApi = {
  send: (message: string, caseId?: number, module?: string) =>
    api.post<ChatResponse>('/api/chat/message', { message, case_id: caseId, module }),
}

// ─── Chat WebSocket ──────────────────────────────────────────────────────────

export class ChatWebSocket {
  private ws: WebSocket | null = null
  private url: string

  constructor(token: string) {
    const wsBase = BASE_URL.replace('http', 'ws')
    this.url = `${wsBase}/api/chat/ws?token=${token}`
  }

  connect(
    onMessage: (data: ChatResponse) => void,
    onClose?: () => void,
    onError?: () => void
  ) {
    this.ws = new WebSocket(this.url)

    this.ws.onmessage = (event) => {
      try {
        onMessage(JSON.parse(event.data))
      } catch { /* ignore parse errors */ }
    }

    this.ws.onclose = () => onClose?.()
    this.ws.onerror = () => onError?.()

    return this
  }

  send(message: string, caseId?: number, module?: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ message, case_id: caseId, module }))
    }
  }

  disconnect() {
    this.ws?.close()
    this.ws = null
  }

  get isConnected() {
    return this.ws?.readyState === WebSocket.OPEN
  }
}
