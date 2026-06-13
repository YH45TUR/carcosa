// Sistema Legal CO - Case Detail
import { useState, useEffect, type ReactNode } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { api } from '../../services/api'
import type { Case, LegalArea } from '../../types'
import { FileUpload } from '../Documents/FileUpload'
import { ExportButton } from '../Documents/ExportButton'
import { EmptyState } from '../ui/EmptyState'
import { SkeletonDetail } from '../ui/Skeleton'
import {
  ArrowLeft, Edit, Trash2, FileText, Calendar,
  Clock, Scale, MessageSquare, Upload
} from 'lucide-react'

const LEGAL_AREA_LABELS: Record<LegalArea, string> = {
  civil: 'Civil',
  penal: 'Penal',
  laboral: 'Laboral',
  administrativo: 'Administrativo',
  constitucional: 'Constitucional',
  familia: 'Familia',
  comercial: 'Comercial',
}

const STATUS_COLORS: Record<string, string> = {
  activo: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  archivado: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  cerrado: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
}

type Tab = 'info' | 'documents' | 'timeline' | 'terms' | 'chat'

export function CaseDetail() {
  const { caseId } = useParams()
  const navigate = useNavigate()
  const [caseData, setCaseData] = useState<Case | null>(null)
  const [activeTab, setActiveTab] = useState<Tab>('info')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (caseId) {
      loadCase(Number(caseId))
    }
  }, [caseId])

  const loadCase = async (id: number) => {
    setIsLoading(true)
    try {
      const data = await api.getCase(id)
      setCaseData(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al cargar el caso')
    } finally {
      setIsLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!caseData || !window.confirm('¿Estás seguro de eliminar este caso? Esta acción no se puede deshacer.')) return

    try {
      await api.deleteCase(caseData.id)
      navigate('/cases')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al eliminar el caso')
    }
  }

  if (isLoading) {
    return <SkeletonDetail />
  }

  if (error || !caseData) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8">
        <div className="p-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-red-700 dark:text-red-300">
          {error || 'Caso no encontrado'}
        </div>
        <button
          onClick={() => navigate('/cases')}
          className="mt-4 inline-flex items-center gap-2 text-legal-600 hover:text-legal-700"
        >
          <ArrowLeft className="w-4 h-4" />
          Volver a casos
        </button>
      </div>
    )
  }

  const tabs: { id: Tab; label: string; icon: ReactNode }[] = [
    { id: 'info', label: 'Información', icon: <FileText className="w-4 h-4" /> },
    { id: 'documents', label: 'Documentos', icon: <FileText className="w-4 h-4" /> },
    { id: 'timeline', label: 'Cronología', icon: <Calendar className="w-4 h-4" /> },
    { id: 'terms', label: 'Términos', icon: <Clock className="w-4 h-4" /> },
    { id: 'chat', label: 'Chat Legal', icon: <MessageSquare className="w-4 h-4" /> },
  ]

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/cases')}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {caseData.cliente}
            </h1>
            <p className="text-gray-600 dark:text-gray-400 text-sm">
              Caso #{caseData.id} · Creado {new Date(caseData.created_at).toLocaleDateString('es-CO')}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Link
            to={`/cases/${caseData.id}/edit`}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors text-gray-600 dark:text-gray-400"
            title="Editar caso"
          >
            <Edit className="w-5 h-5" />
          </Link>
          <button
            onClick={handleDelete}
            className="p-2 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg transition-colors text-red-600"
            title="Eliminar caso"
          >
            <Trash2 className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Status Badge */}
      <div className="mb-6">
        <span className={`text-sm font-medium px-3 py-1.5 rounded-full ${STATUS_COLORS[caseData.status]}`}>
          {caseData.status}
        </span>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700 mb-6">
        <nav className="flex gap-1 -mb-px">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`inline-flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-legal-600 text-legal-600 dark:text-legal-400 dark:border-legal-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 hover:border-gray-300'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'info' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-4">Datos del Caso</h3>
            <dl className="space-y-4">
              <div>
                <dt className="text-sm text-gray-500 dark:text-gray-400">Cliente</dt>
                <dd className="text-gray-900 dark:text-gray-100 font-medium">{caseData.cliente}</dd>
              </div>
              {caseData.demandado && (
                <div>
                  <dt className="text-sm text-gray-500 dark:text-gray-400">Demandado</dt>
                  <dd className="text-gray-900 dark:text-gray-100">{caseData.demandado}</dd>
                </div>
              )}
              <div>
                <dt className="text-sm text-gray-500 dark:text-gray-400">Rama del Derecho</dt>
                <dd className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-legal-50 dark:bg-legal-900/30 text-legal-700 dark:text-legal-300 rounded text-sm font-medium">
                  <Scale className="w-3.5 h-3.5" />
                  {LEGAL_AREA_LABELS[caseData.area] || caseData.area}
                </dd>
              </div>
              {caseData.radicado && (
                <div>
                  <dt className="text-sm text-gray-500 dark:text-gray-400">Radicado</dt>
                  <dd className="text-gray-900 dark:text-gray-100 font-mono text-sm">{caseData.radicado}</dd>
                </div>
              )}
              {caseData.juzgado && (
                <div>
                  <dt className="text-sm text-gray-500 dark:text-gray-400">Juzgado</dt>
                  <dd className="text-gray-900 dark:text-gray-100">{caseData.juzgado}</dd>
                </div>
              )}
              {caseData.cuantia && (
                <div>
                  <dt className="text-sm text-gray-500 dark:text-gray-400">Cuantía</dt>
                  <dd className="text-gray-900 dark:text-gray-100 font-medium">
                    ${caseData.cuantia.toLocaleString('es-CO', { minimumFractionDigits: 2 })}
                  </dd>
                </div>
              )}
            </dl>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-4">Descripción</h3>
            {caseData.description ? (
              <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{caseData.description}</p>
            ) : (
              <p className="text-gray-400 dark:text-gray-500 italic">Sin descripción</p>
            )}
          </div>
        </div>
      )}

      {activeTab === 'documents' && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
              <Upload className="w-5 h-5 text-legal-600" />
              Subir Documentos
            </h3>
            <FileUpload caseId={caseData.id} />
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
              <FileText className="w-5 h-5 text-legal-600" />
              Exportar Documentos
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
              Genera documentos legales en formato Word o PDF con formato NTC 1486.
            </p>
            <ExportButton />
          </div>
        </div>
      )}

      {activeTab === 'timeline' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
            <Calendar className="w-5 h-5 text-legal-600" />
            Cronología del Caso
          </h3>
          <EmptyState
            icon={<Calendar className="w-8 h-8" />}
            title="Sin eventos registrados"
            description="Los eventos procesales aparecerán aquí automáticamente cuando se procesen documentos del caso."
            action={
              <Link
                to={`/chat?caseId=${caseData.id}`}
                className="inline-flex items-center gap-2 px-4 py-2 bg-legal-600 text-white rounded-lg hover:bg-legal-700 transition-colors text-sm font-medium"
              >
                <MessageSquare className="w-4 h-4" />
                Consultar al asistente
              </Link>
            }
          />
        </div>
      )}

      {activeTab === 'terms' && (
        <div className="space-y-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
              <Clock className="w-5 h-5 text-legal-600" />
              Términos Procesales
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
                <h4 className="font-medium text-amber-800 dark:text-amber-300 text-sm mb-1">📋 CGP</h4>
                <p className="text-xs text-amber-600 dark:text-amber-400">Código General del Proceso</p>
                <ul className="mt-2 space-y-1">
                  <li className="text-xs text-amber-700 dark:text-amber-300">• Traslado demanda: 20 días</li>
                  <li className="text-xs text-amber-700 dark:text-amber-300">• Apelación: 5 días</li>
                  <li className="text-xs text-amber-700 dark:text-amber-300">• Reposición: 3 días</li>
                </ul>
              </div>
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <h4 className="font-medium text-blue-800 dark:text-blue-300 text-sm mb-1">⚖️ CPACA</h4>
                <p className="text-xs text-blue-600 dark:text-blue-400">Código Contencioso Administrativo</p>
                <ul className="mt-2 space-y-1">
                  <li className="text-xs text-blue-700 dark:text-blue-300">• Caducidad nulidad: 4 meses</li>
                  <li className="text-xs text-blue-700 dark:text-blue-300">• Apelación: 10 días</li>
                  <li className="text-xs text-blue-700 dark:text-blue-300">• Silencio adm.: 3 meses</li>
                </ul>
              </div>
              <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                <h4 className="font-medium text-red-800 dark:text-red-300 text-sm mb-1">⚔️ CPP</h4>
                <p className="text-xs text-red-600 dark:text-red-400">Código de Procedimiento Penal</p>
                <ul className="mt-2 space-y-1">
                  <li className="text-xs text-red-700 dark:text-red-300">• Imputación: 2 años</li>
                  <li className="text-xs text-red-700 dark:text-red-300">• Apelación sentencia: 5 días</li>
                  <li className="text-xs text-red-700 dark:text-red-300">• Detención preventiva: 1 año</li>
                </ul>
              </div>
              <div className="p-4 bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg">
                <h4 className="font-medium text-purple-800 dark:text-purple-300 text-sm mb-1">🛡️ Guardado</h4>
                <p className="text-xs text-purple-600 dark:text-purple-400">Términos almacenados del caso</p>
                <p className="text-xs text-purple-500 dark:text-purple-400 mt-2 italic">
                  Consulta los términos calculados en el chat legal.
                </p>
              </div>
            </div>
            <div className="mt-4">
              <Link
                to={`/chat?caseId=${caseData.id}`}
                className="inline-flex items-center gap-2 text-sm text-legal-600 hover:text-legal-700 font-medium"
              >
                <MessageSquare className="w-4 h-4" />
                Calcular términos para este caso
              </Link>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'chat' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-8 text-center">
          <MessageSquare className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
          <h3 className="font-medium text-gray-600 dark:text-gray-400">Chat Legal</h3>
          <p className="text-gray-500 dark:text-gray-500 text-sm mt-1 mb-6">
            Consulta con IA legal sobre este caso. Puedes redactar documentos, 
            analizar jurisprudencia, auditar textos y más.
          </p>
          <Link
            to={`/chat?caseId=${caseData.id}`}
            className="inline-flex items-center gap-2 px-6 py-3 bg-legal-600 text-white rounded-xl hover:bg-legal-700 transition-colors font-medium shadow-sm hover:shadow-md"
          >
            <MessageSquare className="w-5 h-5" />
            Abrir Chat Legal
          </Link>
          <div className="mt-8 grid grid-cols-2 gap-3 max-w-lg mx-auto">
            {[
              { icon: '📝', text: 'Redactar demanda' },
              { icon: '🔍', text: 'Auditar documento' },
              { icon: '⚖️', text: 'Buscar jurisprudencia' },
              { icon: '📊', text: 'Generar diagrama' },
            ].map((item) => (
              <Link
                key={item.text}
                to={`/chat?caseId=${caseData.id}`}
                className="px-4 py-3 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-700 rounded-xl text-sm text-gray-600 dark:text-gray-400 hover:border-legal-300 dark:hover:border-legal-700 hover:shadow-sm transition-all text-left flex items-center gap-2"
              >
                <span>{item.icon}</span>
                <span>{item.text}</span>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
