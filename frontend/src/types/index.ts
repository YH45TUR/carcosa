// Tipos centrales del Sistema Legal CO

export interface User {
  id: number
  username: string
  email: string
  role: 'admin' | 'abogado' | 'asistente'
  is_active: boolean
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
}

export type LegalArea =
  | 'civil' | 'penal' | 'laboral' | 'administrativo'
  | 'constitucional' | 'familia' | 'comercial' | 'otro'

export type CaseStatus = 'activo' | 'archivado' | 'cerrado'

export interface Case {
  id: number
  radicado?: string
  cliente: string
  demandado?: string
  area: LegalArea
  status: CaseStatus
  juzgado?: string
  cuantia?: number
  description?: string
  created_at: string
}

export interface CaseCreate {
  cliente: string
  demandado?: string
  area: LegalArea
  radicado?: string
  juzgado?: string
  cuantia?: number
  description?: string
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  module?: string
  data?: Record<string, unknown>
  timestamp: Date
}

export interface ChatResponse {
  message: string
  module: string
  data?: Record<string, unknown>
}

export interface ApiError {
  detail: string
  status?: number
}
