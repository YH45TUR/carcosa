// Sistema Legal CO - Empty State
import type { ReactNode } from 'react'
import { clsx } from 'clsx'

interface Props {
  icon: ReactNode
  title: string
  description?: string
  action?: ReactNode
  className?: string
}

export function EmptyState({ icon, title, description, action, className }: Props) {
  return (
    <div className={clsx('flex flex-col items-center justify-center py-16 text-center', className)}>
      <div className="w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-4">
        <div className="text-gray-300 dark:text-gray-600 [&>svg]:w-8 [&>svg]:h-8">
          {icon}
        </div>
      </div>
      <h3 className="text-lg font-medium text-gray-600 dark:text-gray-400 mb-1">
        {title}
      </h3>
      {description && (
        <p className="text-gray-500 dark:text-gray-500 text-sm mb-6 max-w-md">
          {description}
        </p>
      )}
      {action}
    </div>
  )
}
