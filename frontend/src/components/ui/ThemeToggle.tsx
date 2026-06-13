import { Sun, Moon, Monitor } from 'lucide-react'
import { useTheme, useResolvedTheme } from '../../hooks/useTheme'
import { clsx } from 'clsx'

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  const resolved = useResolvedTheme()

  const options = [
    { value: 'light' as const, icon: Sun, label: 'Modo claro' },
    { value: 'dark' as const, icon: Moon, label: 'Modo oscuro' },
    { value: 'system' as const, icon: Monitor, label: 'Sistema' },
  ]

  return (
    <div className="flex items-center gap-1 p-1 bg-gray-100 dark:bg-gray-800 rounded-lg">
      {options.map(({ value, icon: Icon, label }) => (
        <button
          key={value}
          onClick={() => setTheme(value)}
          className={clsx(
            'p-1.5 rounded-md transition-all duration-200',
            theme === value
              ? 'bg-white dark:bg-gray-700 shadow-sm text-blue-600 dark:text-blue-400'
              : 'text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700/50'
          )}
          title={label}
          aria-label={label}
        >
          <Icon className="w-3.5 h-3.5" />
        </button>
      ))}
      <span className="text-[10px] text-gray-400 dark:text-gray-500 ml-1 hidden sm:inline">
        {resolved === 'dark' ? '🌙' : '☀️'}
      </span>
    </div>
  )
}

export function ThemeToggleSimple() {
  const { toggle } = useTheme()
  const resolved = useResolvedTheme()

  return (
    <button
      onClick={toggle}
      className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-all duration-200"
      title={resolved === 'dark' ? 'Modo claro' : 'Modo oscuro'}
      aria-label="Cambiar tema"
    >
      {resolved === 'dark' ? (
        <Sun className="w-4 h-4" />
      ) : (
        <Moon className="w-4 h-4" />
      )}
    </button>
  )
}
