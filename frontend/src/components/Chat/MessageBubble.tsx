import { format } from 'date-fns'
import { es } from 'date-fns/locale'
import ReactMarkdown from 'react-markdown'
import { Bot, User } from 'lucide-react'
import type { ChatMessage } from '../../types'
import { clsx } from 'clsx'

interface Props {
  message: ChatMessage
}

const MODULE_LABELS: Record<string, string> = {
  drafting: 'Redacción',
  extraction: 'Extracción',
  audit: 'Auditoría',
  testimony: 'Testimonios',
  adversarial: 'Análisis Adversarial',
  jurisprudence: 'Jurisprudencia',
  diagram: 'Diagrama',
  calculator: 'Calculadora',
  timeline: 'Timeline',
  redteam: 'Verificador',
  chat: 'Asistente',
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user'

  return (
    <div className={clsx('flex gap-3 mb-4', isUser && 'flex-row-reverse')}>
      {/* Avatar */}
      <div
        className={clsx(
          'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
          isUser ? 'bg-blue-600' : 'bg-gray-700'
        )}
      >
        {isUser ? (
          <User className="w-4 h-4 text-white" />
        ) : (
          <Bot className="w-4 h-4 text-white" />
        )}
      </div>

      {/* Bubble */}
      <div className={clsx('max-w-[75%]', isUser && 'items-end flex flex-col')}>
        {!isUser && message.module && (
          <span className="text-xs text-gray-400 mb-1 ml-1">
            {MODULE_LABELS[message.module] ?? message.module}
          </span>
        )}

        <div
          className={clsx(
            'rounded-2xl px-4 py-3 text-sm',
            isUser
              ? 'bg-blue-600 dark:bg-blue-700 text-white rounded-tr-sm shadow-md shadow-blue-600/20'
              : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200 rounded-tl-sm shadow-sm'
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <ReactMarkdown className="prose prose-sm max-w-none prose-gray dark:prose-invert">
              {message.content}
            </ReactMarkdown>
          )}
        </div>

        <span className="text-xs text-gray-400 mt-1 mx-1">
          {format(message.timestamp, 'HH:mm', { locale: es })}
        </span>
      </div>
    </div>
  )
}
