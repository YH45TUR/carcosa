// Sistema Legal CO - Loading Spinner
import { clsx } from 'clsx'
import { Loader2 } from 'lucide-react'

interface Props {
  size?: 'sm' | 'md' | 'lg'
  className?: string
  text?: string
}

export function LoadingSpinner({ size = 'md', className, text }: Props) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  }

  return (
    <div className={clsx('flex flex-col items-center justify-center gap-3', className)}>
      <Loader2 className={clsx('animate-spin text-legal-600 dark:text-legal-400', sizeClasses[size])} />
      {text && (
        <p className="text-sm text-gray-500 dark:text-gray-400">{text}</p>
      )}
    </div>
  )
}

export function LoadingPage() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <LoadingSpinner size="lg" text="Cargando..." />
    </div>
  )
}

export function LoadingInline() {
  return (
    <div className="flex items-center justify-center py-8">
      <LoadingSpinner size="sm" />
    </div>
  )
}
