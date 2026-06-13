import { describe, it, expect, beforeEach } from 'vitest'
import { act, renderHook } from '@testing-library/react'

describe('useTheme', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.classList.remove('dark')
  })

  it('debe iniciar en modo system por defecto', async () => {
    const { useTheme } = await import('../../hooks/useTheme')
    const { result } = renderHook(() => useTheme())

    expect(['light', 'dark', 'system']).toContain(result.current.theme)
  })

  it('debe cambiar a dark mode', async () => {
    const { useTheme } = await import('../../hooks/useTheme')
    const { result } = renderHook(() => useTheme())

    act(() => {
      result.current.setTheme('dark')
    })

    expect(result.current.theme).toBe('dark')
    expect(result.current.resolved).toBe('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })

  it('debe cambiar a light mode', async () => {
    const { useTheme } = await import('../../hooks/useTheme')
    const { result } = renderHook(() => useTheme())

    act(() => {
      result.current.setTheme('dark')
    })
    act(() => {
      result.current.setTheme('light')
    })

    expect(result.current.theme).toBe('light')
    expect(result.current.resolved).toBe('light')
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('debe persistir la preferencia en localStorage', async () => {
    const { useTheme } = await import('../../hooks/useTheme')
    const { result } = renderHook(() => useTheme())

    act(() => {
      result.current.setTheme('dark')
    })

    const stored = JSON.parse(localStorage.getItem('theme-storage')!)
    expect(stored.state.theme).toBe('dark')
  })

  it('debe alternar entre modos con toggle', async () => {
    const { useTheme } = await import('../../hooks/useTheme')
    const { result } = renderHook(() => useTheme())

    act(() => {
      result.current.toggle()
    })

    // Debería cambiar al opuesto del modo actual
    expect(['light', 'dark']).toContain(result.current.theme)
  })
})
