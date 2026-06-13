// Sistema Legal CO - Error Message
import { AlertCircle, RefreshCw } from 'lucide-react'

interface Props {
  message: string
  details?: string
  onRetry?: () => void
}

export function ErrorMessage({ message, details, onRetry }: Props) {
  return (
    <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-red-800 dark:text-red-300">
            {message}
          </p>
          {details && (
            <p className="text-xs text-red-600 dark:text-red-400 mt-1">
              {details}
            </p>
          )}
        </div>
        {onRetry && (
          <button
            onClick={onRetry}
            className="shrink-0 p-1.5 hover:bg-red-100 dark:hover:bg-red-900/40 rounded-lg transition-colors"
            title="Reintentar"
          >
            <RefreshCw className="w-4 h-4 text-red-500" />
          </button>
        )}
      </div>
    </div>
  )
}
