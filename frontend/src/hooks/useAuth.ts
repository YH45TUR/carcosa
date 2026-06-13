// Sistema Legal CO - Auth Hook
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '../types'
import { api } from '../services/api'

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  register: (data: { username: string; email: string; password: string; role?: string }) => Promise<void>
  logout: () => void
  checkAuth: () => Promise<void>
}

export const useAuth = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isLoading: true,

      login: async (username: string, password: string) => {
        const tokens = await api.login(username, password)
        localStorage.setItem('access_token', tokens.access_token)
        localStorage.setItem('refresh_token', tokens.refresh_token)

        const userData = await api.getMe()
        set({ user: userData, isAuthenticated: true })
      },

      register: async (data) => {
        const tokens = await api.register(data)
        localStorage.setItem('access_token', tokens.access_token)
        localStorage.setItem('refresh_token', tokens.refresh_token)

        const userData = await api.getMe()
        set({ user: userData, isAuthenticated: true })
      },

      logout: () => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        set({ user: null, isAuthenticated: false })
      },

      checkAuth: async () => {
        const token = localStorage.getItem('access_token')
        if (!token) {
          set({ isLoading: false, isAuthenticated: false })
          return
        }

        try {
          const userData = await api.getMe()
          set({ user: userData, isAuthenticated: true, isLoading: false })
        } catch {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          set({ user: null, isAuthenticated: false, isLoading: false })
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)
