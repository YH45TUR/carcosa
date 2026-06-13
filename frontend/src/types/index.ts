// Sistema Legal CO - TypeScript Types

export interface User {
  id: number
  username: string
  email: string
  role: 'admin' | 'abogado' | 'asistente'
  is_active: boolean
  created_at: string
}

export interface Token {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface Case {
  id: number
  radicado: string | null
  cliente: string
  demandado: string | null
  area: LegalArea
  status: CaseStatus
  juzgado: string | null
  cuantia: number | null
  description: string | null
  created_at: string
  updated_at: string
}

export type LegalArea = 
  | 'civil' 
  | 'penal' 
  | 'laboral' 
  | 'administrativo' 
  | 'constitucional' 
  | 'familia' 
  | 'comercial'

export type CaseStatus = 'activo' | 'archivado' | 'cerrado'

export interface CaseDocument {
  id: number
  case_id: number
  filename: string
  original_filename: string
  file_path: string
  file_type: string
  file_size: number
  extracted_text: string | null
  extracted_metadata: string | null
  created_at: string
}

export interface CaseVersion {
  id: number
  case_id: number
  document_type: string
  version_number: number
  content: string
  file_path: string | null
  created_at: string
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  module?: string
  data?: any
}

export interface CaseTerm {
  id: number
  case_id: number
  tipo: string
  norma: string
  fecha_inicio: string
  fecha_fin: string
  dias_habiles: number
  code: string
  days_remaining: number | null
  is_expired: boolean
}

export interface TimelineEvent {
  id: number
  case_id: number
  fecha: string
  titulo: string
  descripcion: string | null
  documento_id: number | null
  tipo: string
}