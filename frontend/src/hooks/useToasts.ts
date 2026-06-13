import { create } from 'zustand'

export type ToastType = 'success' | 'error' | 'info' | 'warning'

export interface Toast {
  id: string
  message: string
  type: ToastType
  duration?: number
}

interface ToastState {
  toasts: Toast[]
  addToast: (message: string, type?: ToastType, duration?: number) => void
  removeToast: (id: string) => void
  clearToasts: () => void
}

export function useToasts() {
  const store = toastStore

  return {
    toasts: store((s) => s.toasts),
    success: (msg: string) => store.getState().addToast(msg, 'success'),
    error: (msg: string) => store.getState().addToast(msg, 'error'),
    info: (msg: string) => store.getState().addToast(msg, 'info'),
    warning: (msg: string) => store.getState().addToast(msg, 'warning'),
    remove: (id: string) => store.getState().removeToast(id),
    clear: () => store.getState().clearToasts(),
  }
}

const toastStore = create<ToastState>()((set) => ({
  toasts: [],
  addToast: (message, type = 'info', duration = 4000) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
    set((state) => ({
      toasts: [...state.toasts, { id, message, type, duration }],
    }))
    if (duration > 0) {
      setTimeout(() => {
        set((state) => ({
          toasts: state.toasts.filter((t) => t.id !== id),
        }))
      }, duration)
    }
  },
  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    })),
  clearToasts: () => set({ toasts: [] }),
}))
