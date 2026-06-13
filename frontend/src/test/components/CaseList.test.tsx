import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { CaseList } from '../../components/Cases/CaseList'

// Mock casesApi
vi.mock('../../services/api', () => ({
  casesApi: {
    list: vi.fn().mockResolvedValue({
      data: [
        {
          id: 1, cliente: 'Juan Pérez', demandado: 'María García',
          area: 'civil', status: 'activo', radicado: '123-45',
          created_at: '2024-01-15T00:00:00', juzgado: null, cuantia: null, description: null,
        },
        {
          id: 2, cliente: 'Ana Rodríguez', demandado: null,
          area: 'constitucional', status: 'activo', radicado: null,
          created_at: '2024-02-20T00:00:00', juzgado: null, cuantia: null, description: null,
        },
      ],
    }),
  },
}))

// Mock useAuth
vi.mock('../../hooks/useAuth', () => ({
  useAuth: () => ({
    user: { username: 'admin', role: 'admin' },
    logout: vi.fn(),
  }),
}))

// Mock lucide-react
vi.mock('lucide-react', () => ({
  Plus: () => <span>+</span>,
  Folder: () => <span>📁</span>,
  MessageSquare: () => <span>💬</span>,
  Scale: () => <span>⚖️</span>,
  LogOut: () => <span>🚪</span>,
  Search: () => <span>🔍</span>,
  Sun: () => <span>☀️</span>,
  Moon: () => <span>🌙</span>,
  Monitor: () => <span>🖥️</span>,
}))

function renderCaseList() {
  return render(
    <BrowserRouter>
      <CaseList />
    </BrowserRouter>
  )
}

describe('CaseList', () => {
  it('debe renderizar el título y contador', async () => {
    renderCaseList()
    // Buscar por heading (h1) en lugar de texto duplicado
    const headings = await screen.findAllByRole('heading', { level: 1 })
    expect(headings[0]).toHaveTextContent('Casos')
    expect(await screen.findByText(/2 casos en total/)).toBeInTheDocument()
  })

  it('debe mostrar los casos de la API', async () => {
    renderCaseList()
    expect(await screen.findByText('Juan Pérez')).toBeInTheDocument()
    expect(await screen.findByText('Ana Rodríguez')).toBeInTheDocument()
  })

  it('debe mostrar el botón de nuevo caso', async () => {
    renderCaseList()
    expect(await screen.findByText('Nuevo caso')).toBeInTheDocument()
  })

  it('debe mostrar el nombre del usuario en el sidebar', async () => {
    renderCaseList()
    // admin aparece como username y como role - usar getAllByText
    const adminElements = await screen.findAllByText('admin')
    expect(adminElements.length).toBeGreaterThanOrEqual(1)
  })
})
