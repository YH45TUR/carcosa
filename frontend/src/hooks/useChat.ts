import { useState, useEffect, useRef, useCallback } from 'react'
import { ChatWebSocket, chatApi } from '../services/api'
import { useAuth } from './useAuth'
import type { ChatMessage } from '../types'

export function useChat(caseId?: number) {
  const { accessToken } = useAuth()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef<ChatWebSocket | null>(null)

  // Intentar WebSocket si hay token
  useEffect(() => {
    if (!accessToken) return

    const ws = new ChatWebSocket(accessToken)
    ws.connect(
      (data) => {
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: data.message,
            module: data.module,
            data: data.data,
            timestamp: new Date(),
          },
        ])
        setIsLoading(false)
      },
      () => setIsConnected(false),
      () => setIsConnected(false)
    )
    wsRef.current = ws
    setIsConnected(true)

    return () => ws.disconnect()
  }, [accessToken])

  const sendMessage = useCallback(
    async (content: string, module?: string) => {
      if (!content.trim()) return

      const userMsg: ChatMessage = {
        role: 'user',
        content,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, userMsg])
      setIsLoading(true)

      // Preferir WebSocket si está conectado
      if (wsRef.current?.isConnected) {
        wsRef.current.send(content, caseId, module)
        return
      }

      // Fallback REST
      try {
        const { data } = await chatApi.send(content, caseId, module)
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: data.message,
            module: data.module,
            data: data.data,
            timestamp: new Date(),
          },
        ])
      } catch (err) {
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: 'Error al procesar el mensaje. Intenta de nuevo.',
            timestamp: new Date(),
          },
        ])
      } finally {
        setIsLoading(false)
      }
    },
    [caseId]
  )

  const clearMessages = useCallback(() => setMessages([]), [])

  return { messages, isLoading, isConnected, sendMessage, clearMessages }
}
