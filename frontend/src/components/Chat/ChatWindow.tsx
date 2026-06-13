// Sistema Legal CO - Chat Window
import { useRef, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useChat } from '../../hooks/useChat'
import { useVirtualList } from '../../hooks/useVirtualList'
import { MessageBubble } from './MessageBubble'
import { InputArea } from './InputArea'
import { Bot, ArrowDown } from 'lucide-react'

const MESSAGE_HEIGHT = 100 // altura estimada por mensaje

export function ChatWindow() {
  const [searchParams] = useSearchParams()
  const caseId = searchParams.get('caseId') ? Number(searchParams.get('caseId')) : undefined
  const { messages, isLoading, sendMessage, clearMessages } = useChat(caseId)
  const scrollRef = useRef<HTMLDivElement>(null)

  const { visibleItems, totalHeight, offsetY, isNearBottom, scrollToBottom, handleScroll } =
    useVirtualList({
      items: messages,
      itemHeight: MESSAGE_HEIGHT,
      overscan: 3,
      containerRef: scrollRef,
    })

  const suggestions = useMemo(() => [
    'Redacta una demanda civil',
    'Busca jurisprudencia sobre tutela',
    'Audita este documento legal',
    'Calcula términos procesales',
  ], [])

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] max-w-5xl mx-auto">
      {/* Header */}
      <div className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-legal-100 dark:bg-legal-900/50 flex items-center justify-center">
              <Bot className="w-6 h-6 text-legal-600 dark:text-legal-400" />
            </div>
            <div>
              <h2 className="font-semibold text-gray-900 dark:text-gray-100">
                Asistente Legal CO
              </h2>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {caseId ? `Caso #${caseId}` : 'Chat general'} · IA especializada en derecho colombiano
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {messages.length > 0 && (
              <button
                onClick={clearMessages}
                className="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 transition-colors"
              >
                Limpiar chat
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Messages con virtual scrolling */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto bg-gray-50/50 dark:bg-gray-900/50 relative"
      >
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-6">
            <Bot className="w-16 h-16 text-gray-300 dark:text-gray-600 mb-4" />
            <h3 className="text-lg font-medium text-gray-600 dark:text-gray-400 mb-2">
              ¿En qué puedo ayudarte?
            </h3>
            <p className="text-gray-500 dark:text-gray-500 max-w-md text-sm">
              Puedes redactar documentos, analizar jurisprudencia, auditar textos legales,
              calcular términos procesales y más.
            </p>
            <div className="mt-6 grid grid-cols-2 gap-3 max-w-lg">
              {suggestions.map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => sendMessage(suggestion)}
                  className="px-4 py-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm text-gray-700 dark:text-gray-300 hover:border-legal-300 dark:hover:border-legal-700 hover:shadow-sm transition-all text-left"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="relative px-6 py-6">
            {/* Spacer superior para mantener scroll position */}
            {offsetY > 0 && <div style={{ height: offsetY }} />}

            <div className="space-y-4">
              {visibleItems.map((msg, idx) => (
                <MessageBubble key={idx} message={msg} />
              ))}
            </div>

            {/* Spacer inferior */}
            {totalHeight - offsetY - visibleItems.length * MESSAGE_HEIGHT > 0 && (
              <div
                style={{
                  height: Math.max(
                    0,
                    totalHeight - offsetY - visibleItems.length * MESSAGE_HEIGHT
                  ),
                }}
              />
            )}

            {/* Indicador de carga */}
            {isLoading && (
              <div className="flex gap-3 mt-4">
                <div className="w-9 h-9 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center shrink-0">
                  <Bot className="w-5 h-5 text-gray-500" />
                </div>
                <div className="bg-gray-100 dark:bg-gray-700 rounded-2xl rounded-tl-md px-4 py-3">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                  </div>
                </div>
              </div>
            )}

            {/* Indicador de nuevos mensajes */}
            {!isNearBottom && messages.length > 0 && (
              <button
                onClick={scrollToBottom}
                className="sticky bottom-4 left-1/2 -translate-x-1/2 mx-auto flex items-center gap-2 px-4 py-2 bg-legal-600 text-white rounded-full shadow-lg hover:bg-legal-700 transition-colors text-sm font-medium"
              >
                <ArrowDown className="w-4 h-4" />
                Nuevos mensajes
              </button>
            )}
          </div>
        )}
      </div>

      {/* Input */}
      <InputArea onSend={sendMessage} isLoading={isLoading} />
    </div>
  )
}
