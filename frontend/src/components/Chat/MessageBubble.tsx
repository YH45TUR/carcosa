// Sistema Legal CO - Message Bubble
import type { ChatMessage } from '../../types'
import { User, Bot, AlertCircle } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

interface Props {
  message: ChatMessage
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user'
  const isSystem = message.role === 'system'
  const isError = message.content.startsWith('Error:')

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''} ${isSystem ? 'opacity-60' : ''}`}>
      {/* Avatar */}
      <div className={`shrink-0 w-9 h-9 rounded-full flex items-center justify-center ${
        isUser
          ? 'bg-legal-100 dark:bg-legal-900/50 text-legal-600 dark:text-legal-400'
          : isError
          ? 'bg-red-100 dark:bg-red-900/50 text-red-600 dark:text-red-400'
          : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
      }`}>
        {isUser ? (
          <User className="w-5 h-5" />
        ) : isError ? (
          <AlertCircle className="w-5 h-5" />
        ) : (
          <Bot className="w-5 h-5" />
        )}
      </div>

      {/* Content */}
      <div className={`max-w-[80%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={`rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-legal-600 text-white rounded-tr-md'
            : isError
            ? 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 rounded-tl-md'
            : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-tl-md'
        }`}>
          {isUser ? (
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* Module badge */}
        {message.module && !isUser && (
          <span className="inline-block mt-1 px-2 py-0.5 text-xs font-medium bg-legal-50 dark:bg-legal-900/30 text-legal-700 dark:text-legal-300 rounded-full">
            {message.module}
          </span>
        )}

        {/* Timestamp */}
        <p className={`text-xs mt-1 text-gray-400 ${isUser ? 'text-right' : 'text-left'}`}>
          {new Date(message.timestamp).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>
    </div>
  )
}
