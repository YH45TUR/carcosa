// Sistema Legal CO - API Service
import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios'
import type { Token } from '../types'

// Vite provides import.meta.env, but tsc may not recognize it
const API_BASE_URL = 'http://localhost:8000'

class ApiClient {
  private client: AxiosInstance
  private refreshTokenPromise: Promise<string> | null = null

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.client.interceptors.request.use(
      (config) => this.attachToken(config),
      (error) => Promise.reject(error)
    )

    this.client.interceptors.response.use(
      (response) => response,
      (error) => this.handleError(error)
    )
  }

  private attachToken(config: InternalAxiosRequestConfig): InternalAxiosRequestConfig {
    const token = localStorage.getItem('access_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  }

  private async handleError(error: any) {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const newToken = await this.refreshAccessToken()
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return this.client(originalRequest)
      } catch (refreshError) {
        this.logout()
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }

  private async refreshAccessToken(): Promise<string> {
    if (this.refreshTokenPromise) {
      return this.refreshTokenPromise
    }

    const refreshToken = localStorage.getItem('refresh_token')
    if (!refreshToken) {
      throw new Error('No refresh token')
    }

    this.refreshTokenPromise = (async () => {
      try {
        const response = await axios.post(`${API_BASE_URL}/api/auth/refresh`, null, {
          headers: { Authorization: `Bearer ${refreshToken}` }
        })
        const { access_token, refresh_token } = response.data
        localStorage.setItem('access_token', access_token)
        localStorage.setItem('refresh_token', refresh_token)
        return access_token
      } finally {
        this.refreshTokenPromise = null
      }
    })()

    return this.refreshTokenPromise
  }

  private logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    window.location.href = '/login'
  }

  // Auth
  async login(username: string, password: string): Promise<Token> {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)

    const response = await this.client.post('/api/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  }

  async register(data: { username: string; email: string; password: string; role?: string }): Promise<Token> {
    const response = await this.client.post('/api/auth/register', data)
    return response.data
  }

  async getMe() {
    const response = await this.client.get('/api/auth/me')
    return response.data
  }

  // Cases
  async getCases(params?: { status?: string; area?: string; cliente?: string; skip?: number; limit?: number }) {
    const response = await this.client.get('/api/cases', { params })
    return response.data
  }

  async getCase(id: number) {
    const response = await this.client.get(`/api/cases/${id}`)
    return response.data
  }

  async createCase(data: any) {
    const response = await this.client.post('/api/cases', data)
    return response.data
  }

  async updateCase(id: number, data: any) {
    const response = await this.client.put(`/api/cases/${id}`, data)
    return response.data
  }

  async deleteCase(id: number) {
    const response = await this.client.delete(`/api/cases/${id}`)
    return response.data
  }

  // Chat
  async sendMessage(message: string, caseId?: number, module?: string) {
    const response = await this.client.post('/api/chat/message', {
      message,
      case_id: caseId,
      module
    })
    return response.data
  }
}

export const api = new ApiClient()
