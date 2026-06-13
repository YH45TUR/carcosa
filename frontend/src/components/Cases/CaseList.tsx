// Sistema Legal CO - Case List
import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../../services/api'
import type { Case, LegalArea, CaseStatus } from '../../types'
import { Plus, Search, Filter, FolderOpen, Calendar, Gavel } from 'lucide-react'

const LEGAL_AREAS: { value: LegalArea; label: string }[] = [
  { value: 'civil', label: 'Civil' },
  { value: 'penal', label: 'Penal' },
  { value: 'laboral', label: 'Laboral' },
  { value: 'administrativo', label: 'Administrativo' },
  { value: 'constitucional', label: 'Constitucional' },
  { value: 'familia', label: 'Familia' },
  { value: 'comercial', label: 'Comercial' },
]

const STATUS_OPTIONS: { value: CaseStatus | ''; label: string }[] = [
  { value: '', label: 'Todos' },
  { value: 'activo', label: 'Activos' },
  { value: 'archivado', label: 'Archivados' },
  { value: 'cerrado', label: 'Cerrados' },
]

const STATUS_COLORS: Record<CaseStatus, string> = {
  activo: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  archivado: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  cerrado: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
}

export function CaseList() {
  const navigate = useNavigate()
  const [cases, setCases] = useState<Case[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchCliente, setSearchCliente] = useState('')
  const [filterStatus, setFilterStatus] = useState<CaseStatus | ''>('')
  const [filterArea, setFilterArea] = useState<LegalArea | ''>('')

  const loadCases = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const params: Record<string, string> = {}
      if (filterStatus) params.status = filterStatus
      if (filterArea) params.area = filterArea
      if (searchCliente) params.cliente = searchCliente

      const data = await api.getCases(params)
      setCases(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al cargar casos')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadCases()
  }, [filterStatus, filterArea])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    loadCases()
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            Mis Casos
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Gestión de expedientes y documentos legales
          </p>
        </div>
        <Link
          to="/cases/new"
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-legal-600 text-white rounded-lg hover:bg-legal-700 transition-colors font-medium"
        >
          <Plus className="w-5 h-5" />
          Nuevo Caso
        </Link>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4 mb-6">
        <form onSubmit={handleSearch} className="flex flex-wrap gap-4 items-end">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Buscar por cliente
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                value={searchCliente}
                onChange={(e) => setSearchCliente(e.target.value)}
                placeholder="Nombre del cliente..."
                className="w-full pl-9 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-legal-500 focus:border-transparent text-sm"
              />
            </div>
          </div>

          <div className="min-w-[150px]">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Estado
            </label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as CaseStatus | '')}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-legal-500 focus:border-transparent text-sm"
            >
              {STATUS_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          <div className="min-w-[150px]">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Área
            </label>
            <select
              value={filterArea}
              onChange={(e) => setFilterArea(e.target.value as LegalArea | '')}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-legal-500 focus:border-transparent text-sm"
            >
              <option value="">Todas</option>
              {LEGAL_AREAS.map((area) => (
                <option key={area.value} value={area.value}>{area.label}</option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm font-medium"
          >
            <Filter className="w-4 h-4 inline mr-1" />
            Filtrar
          </button>
        </form>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      {/* Loading */}
      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 animate-pulse">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-3" />
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-2" />
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-2/3" />
            </div>
          ))}
        </div>
      ) : cases.length === 0 ? (
        <div className="text-center py-16">
          <FolderOpen className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-600 dark:text-gray-400 mb-2">
            No hay casos registrados
          </h3>
          <p className="text-gray-500 dark:text-gray-500 mb-6">
            Crea tu primer caso para comenzar a trabajar.
          </p>
          <Link
            to="/cases/new"
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-legal-600 text-white rounded-lg hover:bg-legal-700 transition-colors font-medium"
          >
            <Plus className="w-5 h-5" />
            Nuevo Caso
          </Link>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {cases.map((caseItem) => (
            <button
              key={caseItem.id}
              onClick={() => navigate(`/cases/${caseItem.id}`)}
              className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md hover:border-legal-300 dark:hover:border-legal-700 transition-all text-left w-full"
            >
              <div className="flex items-start justify-between mb-3">
                <h3 className="font-semibold text-gray-900 dark:text-gray-100 line-clamp-1">
                  {caseItem.cliente}
                </h3>
                <span className={`text-xs font-medium px-2.5 py-1 rounded-full shrink-0 ${STATUS_COLORS[caseItem.status]}`}>
                  {caseItem.status}
                </span>
              </div>

              <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                {caseItem.radicado && (
                  <div className="flex items-center gap-2">
                    <Gavel className="w-4 h-4 shrink-0" />
                    <span className="truncate">{caseItem.radicado}</span>
                  </div>
                )}
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 shrink-0" />
                  <span>{new Date(caseItem.created_at).toLocaleDateString('es-CO')}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 bg-legal-50 dark:bg-legal-900/30 text-legal-700 dark:text-legal-300 rounded text-xs font-medium">
                    {LEGAL_AREAS.find(a => a.value === caseItem.area)?.label || caseItem.area}
                  </span>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
