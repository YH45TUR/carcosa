import { useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import { MessageBubble } from './MessageBubble'
import { InputArea } from './InputArea'
import { useChat } from '../../hooks/useChat'
import { Bot, Wifi, WifiOff, Trash2 } from 'lucide-react'
import { clsx } from 'clsx'

export function ChatWindow() {
  const [searchParams] = useSearchParams()
  const caseId = searchParams.get('case') ? Number(searchParams.get('case')) : undefined
  const { messages, isLoading, isConnected, sendMessage, clearMessages } = useChat(caseId)
  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll al ultimo mensaje
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 bg-white border-b border-gray-200 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-600 rounded-xl">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-semibold text-gray-900">
              Asistente Legal{caseId ? ` — Caso #${caseId}` : ''}
            </h1>
            <div className="flex items-center gap-1.5 mt-0.5">
              {isConnected ? (
                <>
                  <Wifi className="w-3 h-3 text-green-500" />
                  <span className="text-xs text-green-600">Conectado en tiempo real</span>
                </>
              ) : (
                <>
                  <WifiOff className="w-3 h-3 text-amber-500" />
                  <span className="text-xs text-amber-600">Modo REST</span>
                </>
              )}
            </div>
          </div>
        </div>

        {messages.length > 0 && (
          <button
            onClick={clearMessages}
            className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition"
            title="Limpiar conversación"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center gap-3">
            <div className="p-4 bg-blue-50 rounded-2xl">
              <Bot className="w-10 h-10 text-blue-400" />
            </div>
            <p className="text-gray-500 max-w-sm">
              Puedo ayudarte a redactar documentos, analizar expedientes, buscar
              jurisprudencia y calcular términos procesales.
            </p>
            <div className="flex flex-wrap gap-2 justify-center mt-2">
              {[
                'Redactar una demanda civil',
                'Analizar documentos del caso',
                'Buscar jurisprudencia sobre tutela',
                'Calcular términos CGP',
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => sendMessage(suggestion)}
                  className="px-3 py-1.5 text-sm bg-white border border-gray-200 text-gray-600 rounded-full hover:border-blue-300 hover:text-blue-600 transition"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, i) => (
              <MessageBubble key={i} message={msg} />
            ))}
            {isLoading && (
              <div className="flex gap-3 mb-4">
                <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
                  <div className="flex gap-1.5">
                    <span className={clsx('w-2 h-2 rounded-full bg-gray-400 animate-bounce', '[animation-delay:0ms]')} />
                    <span className={clsx('w-2 h-2 rounded-full bg-gray-400 animate-bounce', '[animation-delay:150ms]')} />
                    <span className={clsx('w-2 h-2 rounded-full bg-gray-400 animate-bounce', '[animation-delay:300ms]')} />
                  </div>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </>
        )}
      </div>

      {/* Input */}
      <InputArea onSend={sendMessage} isLoading={isLoading} />
    </div>
  )
}
