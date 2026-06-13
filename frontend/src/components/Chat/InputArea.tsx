import { useState, type KeyboardEvent, type FormEvent } from 'react'
import { Send, Loader2 } from 'lucide-react'

interface Props {
  onSend: (message: string) => void
  isLoading: boolean
  placeholder?: string
}

export function InputArea({ onSend, isLoading, placeholder }: Props) {
  const [value, setValue] = useState('')

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (!value.trim() || isLoading) return
    onSend(value.trim())
    setValue('')
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (!value.trim() || isLoading) return
      onSend(value.trim())
      setValue('')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-3 items-end p-4 border-t border-gray-200 bg-white">
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder ?? 'Escribe tu consulta legal... (Enter para enviar, Shift+Enter para nueva línea)'}
        rows={1}
        disabled={isLoading}
        className="flex-1 px-4 py-2.5 border border-gray-300 rounded-xl resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition text-sm min-h-[44px] max-h-32 overflow-y-auto disabled:opacity-50"
        style={{ height: 'auto' }}
        onInput={(e) => {
          const target = e.currentTarget
          target.style.height = 'auto'
          target.style.height = Math.min(target.scrollHeight, 128) + 'px'
        }}
      />
      <button
        type="submit"
        disabled={!value.trim() || isLoading}
        className="flex-shrink-0 p-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
      >
        {isLoading ? (
          <Loader2 className="w-5 h-5 animate-spin" />
        ) : (
          <Send className="w-5 h-5" />
        )}
      </button>
    </form>
  )
}
