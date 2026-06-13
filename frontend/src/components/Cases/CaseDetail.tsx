import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { casesApi, api } from '../../services/api'
import { FileUpload } from '../Documents/FileUpload'
import type { Case, Document as CaseDoc } from '../../types'
import {
  ArrowLeft, MessageSquare, FileText, Download,
  Trash2, Loader2, CheckCircle, Clock, AlertCircle
} from 'lucide-react'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'

const AREA_LABELS: Record<string, string> = {
  civil: 'Civil', penal: 'Penal', laboral: 'Laboral',
  administrativo: 'Administrativo', constitucional: 'Constitucional',
  familia: 'Familia', comercial: 'Comercial', otro: 'Otro',
}

const STATUS_BADGE: Record<string, { color: string; label: string }> = {
  activo: { color: 'bg-green-100 text-green-700', label: 'Activo' },
  archivado: { color: 'bg-gray-100 text-gray-600', label: 'Archivado' },
  cerrado: { color: 'bg-red-100 text-red-600', label: 'Cerrado' },
}

function DocStatusIcon({ status }: { status: string }) {
  if (status === 'done') return <CheckCircle className="w-4 h-4 text-green-500" />
  if (status === 'error') return <AlertCircle className="w-4 h-4 text-red-500" />
  if (status === 'processing') return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
  return <Clock className="w-4 h-4 text-amber-400" />
}

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function CaseDetail() {
  const { caseId } = useParams<{ caseId: string }>()
  const navigate = useNavigate()
  const [caso, setCaso] = useState<Case | null>(null)
  const [documents, setDocuments] = useState<CaseDoc[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'info' | 'docs'>('info')

  const loadDocuments = async () => {
    if (!caseId) return
    try {
      const { data } = await api.get<CaseDoc[]>(`/api/documents/by-case/${caseId}`)
      setDocuments(data)
    } catch { /* ignore */ }
  }

  useEffect(() => {
    if (!caseId) return
    Promise.all([
      casesApi.get(Number(caseId)).then(({ data }) => setCaso(data)),
      loadDocuments(),
    ]).finally(() => setIsLoading(false))
  }, [caseId])

  const handleDelete = async () => {
    if (!caseId || !confirm('\u00bfEliminar este caso y todos sus documentos?')) return
    await casesApi.delete(Number(caseId))
    navigate('/cases')
  }

  const deleteDocument = async (docId: number) => {
    if (!confirm('\u00bfEliminar este documento?')) return
    await api.delete(`/api/documents/${docId}`)
    setDocuments(prev => prev.filter(d => d.id !== docId))
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

  const badge = STATUS_BADGE[caso.status]

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto p-8">
        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <div className="flex items-center gap-3">
            <button onClick={() => navigate(-1)} className="p-2 hover:bg-gray-200 rounded-lg transition">
              <ArrowLeft className="w-4 h-4 text-gray-600" />
            </button>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold text-gray-900">{caso.cliente}</h1>
                <span className={`text-xs px-2 py-0.5 rounded-full ${badge.color}`}>{badge.label}</span>
              </div>
              {caso.demandado && <p className="text-gray-500 mt-0.5">vs. {caso.demandado}</p>}
            </div>
          </div>
          <div className="flex gap-2">
            <Link
              to={`/chat?case=${caso.id}`}
              className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm transition"
            >
              <MessageSquare className="w-4 h-4" /> Chat IA
            </Link>
            <button
              onClick={handleDelete}
              className="p-2 border border-red-300 text-red-500 rounded-lg hover:bg-red-50 transition"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 border-b border-gray-200">
          {(['info', 'docs'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-sm font-medium -mb-px border-b-2 transition ${
                activeTab === tab
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab === 'info' ? 'Informaci\u00f3n' : `Documentos (${documents.length})`}
            </button>
          ))}
        </div>

        {/* Info tab */}
        {activeTab === 'info' && (
          <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
            <div className="grid grid-cols-2 gap-4">
              {[
                { label: '\u00c1rea', value: AREA_LABELS[caso.area] },
                { label: 'Estado', value: badge.label },
                caso.radicado ? { label: 'Radicado', value: caso.radicado } : null,
                caso.juzgado ? { label: 'Juzgado', value: caso.juzgado } : null,
                caso.cuantia ? { label: 'Cuant\u00eda', value: `$${caso.cuantia.toLocaleString('es-CO')}` } : null,
                { label: 'Creado', value: format(new Date(caso.created_at), "d 'de' MMMM, yyyy", { locale: es }) },
              ].filter(Boolean).map((item) => item && (
                <div key={item.label} className="bg-gray-50 rounded-xl p-4">
                  <p className="text-xs text-gray-400 mb-1">{item.label}</p>
                  <p className="font-medium text-gray-800 text-sm">{item.value}</p>
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
        )}

        {/* Docs tab */}
        {activeTab === 'docs' && (
          <div className="space-y-6">
            {/* Upload */}
            <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
              <h3 className="font-semibold text-gray-800 mb-4">Subir documentos</h3>
              <FileUpload
                caseId={caso.id}
                onUploaded={(doc) => setDocuments(prev => [...prev, doc])}
              />
            </div>

            {/* Document list */}
            {documents.length > 0 && (
              <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
                <h3 className="font-semibold text-gray-800 mb-4">Expediente ({documents.length} archivos)</h3>
                <div className="space-y-2">
                  {documents.map((doc) => (
                    <div key={doc.id} className="flex items-center gap-3 p-3 border border-gray-100 rounded-xl hover:bg-gray-50 transition">
                      <FileText className="w-5 h-5 text-gray-400 shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-800 truncate">{doc.filename}</p>
                        <p className="text-xs text-gray-400">
                          {(doc.file_size / 1024).toFixed(0)} KB · .{doc.file_type}
                          {doc.has_text && ' · Texto extraído'}
                          {doc.has_metadata && ' · Entidades'}
                        </p>
                      </div>
                      <DocStatusIcon status={doc.processing_status} />
                      <a
                        href={`${BASE_URL}/api/documents/${doc.id}/download`}
                        download={doc.filename}
                        className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition"
                        title="Descargar"
                      >
                        <Download className="w-4 h-4" />
                      </a>
                      <button
                        onClick={() => deleteDocument(doc.id)}
                        className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition"
                        title="Eliminar"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {documents.length === 0 && (
              <p className="text-center text-gray-400 py-8">No hay documentos subidos aún.</p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
