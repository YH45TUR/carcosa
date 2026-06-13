import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { LoginForm } from '../../components/Auth/LoginForm'

// Mock useAuth
const mockLogin = vi.fn()
const mockClearError = vi.fn()

// Estado base del mock
let mockState = {
  user: null as any,
  accessToken: null as string | null,
  isLoading: false,
  error: null as string | null,
  login: mockLogin,
  clearError: mockClearError,
}

// Función para actualizar el mock desde tests
function setMockState(overrides: Partial<typeof mockState>) {
  mockState = { ...mockState, ...overrides }
}

vi.mock('../../hooks/useAuth', () => ({
  useAuth: () => mockState,
}))

// Mock lucide-react
vi.mock('lucide-react', () => ({
  Scale: () => <span data-testid="scale-icon" />,
}))

function renderLoginForm() {
  return render(
    <BrowserRouter>
      <LoginForm />
    </BrowserRouter>
  )
}

describe('LoginForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('debe renderizar el formulario de login', () => {
    renderLoginForm()
    expect(screen.getByText('Sistema Legal CO')).toBeInTheDocument()
    expect(screen.getByText('Iniciar sesión')).toBeInTheDocument()
    expect(screen.getByLabelText('Usuario')).toBeInTheDocument()
    expect(screen.getByLabelText('Contraseña')).toBeInTheDocument()
  })

  it('debe tener un botón de ingreso', () => {
    renderLoginForm()
    expect(screen.getByRole('button', { name: /ingresar/i })).toBeInTheDocument()
  })

  it('debe mostrar error cuando hay un error en el store', () => {
    setMockState({ error: 'Credenciales incorrectas' })
    renderLoginForm()
    expect(screen.getByText('Credenciales incorrectas')).toBeInTheDocument()
  })

  it('debe llamar a login cuando se envía el formulario', async () => {
    const user = userEvent.setup()
    mockLogin.mockResolvedValueOnce(undefined)

    renderLoginForm()

    await user.type(screen.getByLabelText('Usuario'), 'admin')
    await user.type(screen.getByLabelText('Contraseña'), 'admin123')
    await user.click(screen.getByRole('button', { name: /ingresar/i }))

    expect(mockLogin).toHaveBeenCalledWith('admin', 'admin123')
  })

  it('debe mostrar "Iniciando sesión..." cuando está cargando', () => {
    setMockState({ isLoading: true })
    renderLoginForm()
    expect(screen.getByText('Iniciando sesión...')).toBeInTheDocument()
  })
})
