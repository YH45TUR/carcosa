// Sistema Legal CO - Chat Hook
import { useState, useCallback } from 'react'
import { api } from '../services/api'
import type { ChatMessage } from '../types'

export function useChat(caseId?: number) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const sendMessage = useCallback(async (content: string, module?: string) => {
    setIsLoading(true)
    setError(null)

    // Agregar mensaje del usuario
    const userMessage: ChatMessage = {
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMessage])

    try {
      const response = await api.sendMessage(content, caseId, module)
      
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.message,
        timestamp: new Date().toISOString(),
        module: response.module,
        data: response.data,
      }
      setMessages(prev => [...prev, assistantMessage])
      
      return response
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Error al enviar mensaje'
      setError(errorMessage)
      
      const errorMsg: ChatMessage = {
        role: 'assistant',
        content: `Error: ${errorMessage}`,
        timestamp: new Date().toISOString(),
      }
      setMessages(prev => [...prev, errorMsg])
    } finally {
      setIsLoading(false)
    }
  }, [caseId])

  const clearMessages = useCallback(() => {
    setMessages([])
    setError(null)
  }, [])

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearMessages,
  }
}