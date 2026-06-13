import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { casesApi } from '../../services/api'
import { useAuth } from '../../hooks/useAuth'
import type { Case } from '../../types'
import { Plus, Folder, MessageSquare, Scale, LogOut, Search } from 'lucide-react'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'

const AREA_LABELS: Record<string, string> = {
  civil: 'Civil', penal: 'Penal', laboral: 'Laboral',
  administrativo: 'Administrativo', constitucional: 'Constitucional',
  familia: 'Familia', comercial: 'Comercial', otro: 'Otro',
}

const STATUS_COLORS: Record<string, string> = {
  activo: 'bg-green-100 text-green-700',
  archivado: 'bg-gray-100 text-gray-600',
  cerrado: 'bg-red-100 text-red-600',
}

export function CaseList() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [cases, setCases] = useState<Case[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [search, setSearch] = useState('')

  useEffect(() => {
    casesApi.list().then(({ data }) => setCases(data)).finally(() => setIsLoading(false))
  }, [])

  const filtered = cases.filter(
    (c) =>
      c.cliente.toLowerCase().includes(search.toLowerCase()) ||
      (c.radicado ?? '').includes(search)
  )

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 w-64 bg-gray-900 text-white flex flex-col">
        <div className="p-6">
          <div className="flex items-center gap-2 mb-8">
            <Scale className="w-6 h-6 text-blue-400" />
            <span className="font-bold text-lg">Sistema Legal CO</span>
          </div>
          <nav className="space-y-1">
            <Link to="/cases" className="flex items-center gap-3 px-3 py-2 rounded-lg bg-gray-800 text-white">
              <Folder className="w-4 h-4" /> Casos
            </Link>
            <Link to="/chat" className="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-400 hover:bg-gray-800 hover:text-white transition">
              <MessageSquare className="w-4 h-4" /> Asistente
            </Link>
          </nav>
        </div>
        <div className="mt-auto p-6 border-t border-gray-800">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-sm font-bold">
              {user?.username[0].toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user?.username}</p>
              <p className="text-xs text-gray-400 capitalize">{user?.role}</p>
            </div>
          </div>
          <button onClick={logout} className="flex items-center gap-2 text-xs text-gray-400 hover:text-white transition">
            <LogOut className="w-3.5 h-3.5" /> Cerrar sesión
          </button>
        </div>
      </div>

      {/* Main */}
      <div className="ml-64 p-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Casos</h1>
            <p className="text-gray-500 mt-1">{cases.length} casos en total</p>
          </div>
          <Link to="/cases/new" className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
            <Plus className="w-4 h-4" /> Nuevo caso
          </Link>
        </div>

        {/* Search */}
        <div className="relative mb-6">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por cliente o radicado..."
            className="w-full pl-10 pr-4 py-2.5 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none"
          />
        </div>

        {isLoading ? (
          <div className="flex justify-center py-20">
            <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-20 text-gray-400">
            {search ? 'No se encontraron casos.' : 'Aún no hay casos. Crea el primero.'}
          </div>
        ) : (
          <div className="grid gap-4">
            {filtered.map((c) => (
              <div
                key={c.id}
                onClick={() => navigate(`/cases/${c.id}`)}
                className="bg-white border border-gray-200 rounded-xl p-5 hover:border-blue-300 hover:shadow-sm cursor-pointer transition"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-gray-900 truncate">{c.cliente}</h3>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_COLORS[c.status]}`}>
                        {c.status}
                      </span>
                    </div>
                    {c.demandado && <p className="text-sm text-gray-500">vs. {c.demandado}</p>}
                    <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                      {c.radicado && <span>Rad. {c.radicado}</span>}
                      <span>{AREA_LABELS[c.area]}</span>
                      <span>{format(new Date(c.created_at), "d 'de' MMMM, yyyy", { locale: es })}</span>
                    </div>
                  </div>
                  <Link
                    to={`/chat?case=${c.id}`}
                    onClick={(e) => e.stopPropagation()}
                    className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition"
                    title="Abrir chat de este caso"
                  >
                    <MessageSquare className="w-4 h-4" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
