// Sistema Legal CO - Case Form
import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../../services/api'
import type { LegalArea } from '../../types'
import { ArrowLeft, Save } from 'lucide-react'

const LEGAL_AREAS: { value: LegalArea; label: string }[] = [
  { value: 'civil', label: 'Civil' },
  { value: 'penal', label: 'Penal' },
  { value: 'laboral', label: 'Laboral' },
  { value: 'administrativo', label: 'Administrativo' },
  { value: 'constitucional', label: 'Constitucional' },
  { value: 'familia', label: 'Familia' },
  { value: 'comercial', label: 'Comercial' },
]

interface FormData {
  cliente: string
  demandado: string
  area: LegalArea | ''
  radicado: string
  juzgado: string
  cuantia: string
  description: string
}

const INITIAL_DATA: FormData = {
  cliente: '',
  demandado: '',
  area: '',
  radicado: '',
  juzgado: '',
  cuantia: '',
  description: '',
}

export function CaseForm() {
  const navigate = useNavigate()
  const { caseId } = useParams()
  const isEditing = Boolean(caseId)

  const [formData, setFormData] = useState<FormData>(INITIAL_DATA)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (caseId) {
      loadCase(Number(caseId))
    }
  }, [caseId])

  const loadCase = async (id: number) => {
    try {
      const caseData = await api.getCase(id)
      setFormData({
        cliente: caseData.cliente,
        demandado: caseData.demandado || '',
        area: caseData.area,
        radicado: caseData.radicado || '',
        juzgado: caseData.juzgado || '',
        cuantia: caseData.cuantia ? String(caseData.cuantia) : '',
        description: caseData.description || '',
      })
    } catch (err: any) {
      setError('Error al cargar el caso')
    }
  }

  const handleChange = (field: keyof FormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)

    try {
      const payload = {
        ...formData,
        cuantia: formData.cuantia ? parseFloat(formData.cuantia) : null,
      }

      if (isEditing) {
        await api.updateCase(Number(caseId), payload)
      } else {
        await api.createCase(payload)
      }

      navigate('/cases')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al guardar el caso')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <button
          onClick={() => navigate('/cases')}
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
        </button>
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            {isEditing ? 'Editar Caso' : 'Nuevo Caso'}
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            {isEditing ? 'Actualiza los datos del expediente' : 'Registra un nuevo expediente legal'}
          </p>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-8 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Cliente */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Cliente <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.cliente}
              onChange={(e) => handleChange('cliente', e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-legal-500 focus:border-transparent"
              required
              placeholder="Nombre completo del cliente"
            />
          </div>

          {/* Demandado */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Demandado / Parte contraria
            </label>
            <input
              type="text"
              value={formData.demandado}
              onChange={(e) => handleChange('demandado', e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-legal-500 focus:border-transparent"
              placeholder="Nombre de la contraparte"
            />
          </div>

          {/* Área */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Rama del Derecho <span className="text-red-500">*</span>
            </label>
            <select
              value={formData.area}
              onChange={(e) => handleChange('area', e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-legal-500 focus:border-transparent"
              required
            >
              <option value="">Seleccionar...</option>
              {LEGAL_AREAS.map((area) => (
                <option key={area.value} value={area.value}>{area.label}</option>
              ))}
            </select>
          </div>

          {/* Radicado */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Número de Radicado
            </label>
            <input
              type="text"
              value={formData.radicado}
              onChange={(e) => handleChange('radicado', e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-legal-500 focus:border-transparent"
              placeholder="Ej: 11001-31-03-001-2024-00001-00"
            />
          </div>

          {/* Juzgado */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Juzgado / Despacho
            </label>
            <input
              type="text"
              value={formData.juzgado}
              onChange={(e) => handleChange('juzgado', e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-legal-500 focus:border-transparent"
              placeholder="Ej: Juzgado 1° Civil del Circuito"
            />
          </div>

          {/* Cuantía */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Cuantía
            </label>
            <input
              type="number"
              value={formData.cuantia}
              onChange={(e) => handleChange('cuantia', e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-legal-500 focus:border-transparent"
              placeholder="Valor en pesos"
              step="0.01"
              min="0"
            />
          </div>
        </div>

        {/* Descripción */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Descripción / Observaciones
          </label>
          <textarea
            value={formData.description}
            onChange={(e) => handleChange('description', e.target.value)}
            rows={4}
            className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-legal-500 focus:border-transparent resize-none"
            placeholder="Describe el caso, hechos relevantes, etc."
          />
        </div>

        {/* Submit */}
        <div className="flex items-center justify-end gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <button
            type="button"
            onClick={() => navigate('/cases')}
            className="px-4 py-2.5 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors font-medium"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={isLoading}
            className="inline-flex items-center gap-2 px-6 py-2.5 bg-legal-600 text-white rounded-lg hover:bg-legal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
          >
            <Save className="w-4 h-4" />
            {isLoading ? 'Guardando...' : isEditing ? 'Actualizar Caso' : 'Crear Caso'}
          </button>
        </div>
      </form>
    </div>
  )
}
