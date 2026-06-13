import { describe, it, expect, vi, beforeEach } from 'vitest'
import { act, renderHook } from '@testing-library/react'

// Mock authApi
const mockLogin = vi.fn()
const mockMe = vi.fn()

vi.mock('../../services/api', () => ({
  authApi: {
    login: mockLogin,
    me: mockMe,
  },
}))

describe('useAuth', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    localStorage.clear()
    // Resetear el store de zustand entre tests
    const { useAuth } = await import('../../hooks/useAuth')
    useAuth.setState({
      user: null,
      accessToken: null,
      refreshToken: null,
      isLoading: false,
      error: null,
    })
  })

  it('debe tener estado inicial correcto', async () => {
    const { useAuth } = await import('../../hooks/useAuth')
    const { result } = renderHook(() => useAuth())

    expect(result.current.user).toBeNull()
    expect(result.current.accessToken).toBeNull()
    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('debe hacer login exitosamente', async () => {
    const tokens = { access_token: 'abc', refresh_token: 'def', token_type: 'bearer' }
    const user = { id: 1, username: 'admin', email: 'admin@test.co', role: 'admin' as const, is_active: true }

    mockLogin.mockResolvedValueOnce({ data: tokens })
    mockMe.mockResolvedValueOnce({ data: user })

    const { useAuth } = await import('../../hooks/useAuth')
    const { result } = renderHook(() => useAuth())

    await act(async () => {
      await result.current.login('admin', 'admin123')
    })

    expect(mockLogin).toHaveBeenCalledWith('admin', 'admin123')
    expect(mockMe).toHaveBeenCalled()
    expect(result.current.user).toEqual(user)
  })

  it('debe manejar error de login', async () => {
    mockLogin.mockRejectedValueOnce({
      response: { data: { detail: 'Credenciales incorrectas' } },
    })

    const { useAuth } = await import('../../hooks/useAuth')
    const { result } = renderHook(() => useAuth())

    await act(async () => {
      await result.current.login('wrong', 'wrong')
    })

    expect(result.current.error).toBe('Credenciales incorrectas')
    expect(result.current.isLoading).toBe(false)
  })

  it('debe hacer logout correctamente', async () => {
    const { useAuth } = await import('../../hooks/useAuth')

    const { result } = renderHook(() => useAuth())

    act(() => {
      result.current.logout()
    })

    expect(result.current.user).toBeNull()
    expect(result.current.accessToken).toBeNull()
    expect(localStorage.getItem('access_token')).toBeNull()
  })
})
