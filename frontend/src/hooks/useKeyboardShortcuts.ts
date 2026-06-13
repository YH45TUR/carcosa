import { useEffect } from 'react'

type ShortcutHandler = (e: KeyboardEvent) => void

interface Shortcut {
  key: string
  ctrl?: boolean
  meta?: boolean
  shift?: boolean
  handler: ShortcutHandler
  description?: string
}

const shortcuts = new Map<string, Shortcut>()

export function registerShortcut(shortcut: Shortcut) {
  const id = `${shortcut.ctrl ? 'ctrl+' : ''}${shortcut.meta ? 'meta+' : ''}${shortcut.shift ? 'shift+' : ''}${shortcut.key}`
  shortcuts.set(id, shortcut)
}

export function unregisterShortcut(key: string) {
  shortcuts.delete(key)
}

export function useKeyboardShortcuts() {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      // No activar shortcuts cuando el usuario está escribiendo en un input
      const target = e.target as HTMLElement
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
        // Excepción: Ctrl+K en inputs sí funciona (búsqueda global)
        if (!(e.key === 'k' && (e.ctrlKey || e.metaKey))) return
      }

      for (const [, shortcut] of shortcuts) {
        const ctrlMatch = shortcut.ctrl ? (e.ctrlKey || e.metaKey) : true
        const shiftMatch = shortcut.shift ? e.shiftKey : true
        const keyMatch = e.key.toLowerCase() === shortcut.key.toLowerCase()

        if (ctrlMatch && shiftMatch && keyMatch) {
          e.preventDefault()
          shortcut.handler(e)
          return
        }
      }
    }

    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [])
}

// Shortcuts predefinidos
export function registerDefaultShortcuts(handlers: {
  onSearch?: () => void
  onNewCase?: () => void
  onGoHome?: () => void
}) {
  if (handlers.onSearch) {
    registerShortcut({
      key: 'k',
      ctrl: true,
      handler: handlers.onSearch,
      description: 'Buscar casos',
    })
  }

  if (handlers.onNewCase) {
    registerShortcut({
      key: 'n',
      ctrl: true,
      handler: handlers.onNewCase,
      description: 'Nuevo caso',
    })
  }

  if (handlers.onGoHome) {
    registerShortcut({
      key: 'g',
      ctrl: true,
      shift: true,
      handler: handlers.onGoHome,
      description: 'Ir a casos',
    })
  }
}
