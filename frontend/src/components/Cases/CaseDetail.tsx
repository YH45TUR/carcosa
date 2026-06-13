import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { casesApi } from '../../services/api'
import type { Case } from '../../types'
import { ArrowLeft, MessageSquare, Edit, Trash2 } from 'lucide-react'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'

const AREA_LABELS: Record<string, string> = {
  civil: 'Civil', penal: 'Penal', laboral: 'Laboral',
  administrativo: 'Administrativo', constitucional: 'Constitucional',
  familia: 'Familia', comercial: 'Comercial', otro: 'Otro',
}

export function CaseDetail() {
  const { caseId } = useParams<{ caseId: string }>()
  const navigate = useNavigate()
  const [caso, setCaso] = useState<Case | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (!caseId) return
    casesApi.get(Number(caseId))
      .then(({ data }) => setCaso(data))
      .finally(() => setIsLoading(false))
  }, [caseId])

  const handleDelete = async () => {
    if (!caseId || !confirm('\u00bfEliminar este caso?')) return
    await casesApi.delete(Number(caseId))
    navigate('/cases')
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!caso) {
    return (
      <div className="p-8 text-center">
        <p className="text-gray-500">Caso no encontrado.</p>
        <Link to="/cases" className="text-blue-600 mt-2 block">Volver a casos</Link>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-gray-500 hover:text-gray-700 transition">
            <ArrowLeft className="w-4 h-4" /> Volver
          </button>
          <div className="flex gap-2">
            <Link
              to={`/chat?case=${caso.id}`}
              className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm transition"
            >
              <MessageSquare className="w-4 h-4" /> Abrir chat
            </Link>
            <Link
              to={`/cases/${caso.id}/edit`}
              className="flex items-center gap-2 px-3 py-2 border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-100 text-sm transition"
            >
              <Edit className="w-4 h-4" /> Editar
            </Link>
            <button
              onClick={handleDelete}
              className="flex items-center gap-2 px-3 py-2 border border-red-300 text-red-600 rounded-lg hover:bg-red-50 text-sm transition"
            >
              <Trash2 className="w-4 h-4" /> Eliminar
            </button>
          </div>
        </div>

        {/* Card */}
        <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
          <h1 className="text-2xl font-bold text-gray-900 mb-1">{caso.cliente}</h1>
          {caso.demandado && <p className="text-gray-500 mb-4">vs. {caso.demandado}</p>}

          <div className="grid grid-cols-2 gap-4 mt-6">
            {[
              { label: '\u00c1rea', value: AREA_LABELS[caso.area] },
              { label: 'Estado', value: caso.status },
              caso.radicado ? { label: 'Radicado', value: caso.radicado } : null,
              caso.juzgado ? { label: 'Juzgado', value: caso.juzgado } : null,
              caso.cuantia ? { label: 'Cuant\u00eda', value: `$${caso.cuantia.toLocaleString('es-CO')}` } : null,
              { label: 'Creado', value: format(new Date(caso.created_at), "d 'de' MMMM, yyyy", { locale: es }) },
            ].filter(Boolean).map((item) => item && (
              <div key={item.label} className="bg-gray-50 rounded-xl p-4">
                <p className="text-xs text-gray-400 mb-1">{item.label}</p>
                <p className="font-medium text-gray-800">{item.value}</p>
              </div>
            ))}
          </div>

          {caso.description && (
            <div className="mt-6">
              <h3 className="text-sm font-medium text-gray-500 mb-2">Descripci\u00f3n</h3>
              <p className="text-gray-700 text-sm leading-relaxed">{caso.description}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
