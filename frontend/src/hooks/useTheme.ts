import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type Theme = 'light' | 'dark' | 'system'

interface ThemeState {
  theme: Theme
  resolved: 'light' | 'dark'
  setTheme: (theme: Theme) => void
  toggle: () => void
}

function getSystemTheme(): 'light' | 'dark' {
  if (typeof window === 'undefined') return 'light'
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function applyTheme(resolved: 'light' | 'dark') {
  const root = document.documentElement
  if (resolved === 'dark') {
    root.classList.add('dark')
  } else {
    root.classList.remove('dark')
  }
}

export const useTheme = create<ThemeState>()(
  persist(
    (set, get) => {
      // Aplicar tema inicial
      const initialTheme = (localStorage.getItem('theme-storage')
        ? JSON.parse(localStorage.getItem('theme-storage')!).state?.theme
        : undefined) as Theme | undefined

      const theme = initialTheme || 'system'
      const resolved = theme === 'system' ? getSystemTheme() : theme
      applyTheme(resolved)

      // Escuchar cambios del sistema
      if (typeof window !== 'undefined') {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
          const { theme } = get()
          if (theme === 'system') {
            const resolved = getSystemTheme()
            applyTheme(resolved)
            set({ resolved })
          }
        })
      }

      return {
        theme,
        resolved,
        setTheme: (theme: Theme) => {
          const resolved = theme === 'system' ? getSystemTheme() : theme
          applyTheme(resolved)
          set({ theme, resolved })
        },
        toggle: () => {
          const { theme, resolved } = get()
          if (theme === 'system') {
            // Si está en system, cambiar al opuesto del actual
            const newTheme = resolved === 'dark' ? 'light' : 'dark'
            applyTheme(newTheme)
            set({ theme: newTheme, resolved: newTheme })
          } else {
            const newTheme = theme === 'dark' ? 'light' : 'dark'
            applyTheme(newTheme)
            set({ theme: newTheme, resolved: newTheme })
          }
        },
      }
    },
    {
      name: 'theme-storage',
      partialize: (state) => ({ theme: state.theme }),
      onRehydrateStorage: () => {
        return (state) => {
          if (state) {
            const resolved = state.theme === 'system' ? getSystemTheme() : state.theme
            applyTheme(resolved)
            state.resolved = resolved
          }
        }
      },
    }
  )
)

// Hook para obtener el tema actual (útil para iconos)
export function useResolvedTheme() {
  return useTheme((s) => s.resolved)
}
