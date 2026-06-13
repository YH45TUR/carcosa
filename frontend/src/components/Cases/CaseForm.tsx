import { useState, type FormEvent, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { casesApi } from '../../services/api'
import type { CaseCreate, LegalArea } from '../../types'
import { ArrowLeft } from 'lucide-react'

const AREAS: { value: LegalArea; label: string }[] = [
  { value: 'civil', label: 'Civil' },
  { value: 'penal', label: 'Penal' },
  { value: 'laboral', label: 'Laboral' },
  { value: 'administrativo', label: 'Administrativo' },
  { value: 'constitucional', label: 'Constitucional' },
  { value: 'familia', label: 'Familia' },
  { value: 'comercial', label: 'Comercial' },
  { value: 'otro', label: 'Otro' },
]

export function CaseForm() {
  const navigate = useNavigate()
  const { caseId } = useParams<{ caseId: string }>()
  const isEditing = !!caseId
  const [isLoading, setIsLoading] = useState(false)
  const [isFetching, setIsFetching] = useState(isEditing)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState<CaseCreate>({
    cliente: '',
    demandado: '',
    area: 'civil',
    radicado: '',
    juzgado: '',
    cuantia: undefined,
    description: '',
  })

  // Cargar datos existentes si es edición
  useEffect(() => {
    if (!caseId) return
    setIsFetching(true)
    casesApi.get(Number(caseId))
      .then(({ data }) => {
        setForm({
          cliente: data.cliente || '',
          demandado: data.demandado || '',
          area: data.area,
          radicado: data.radicado || '',
          juzgado: data.juzgado || '',
          cuantia: data.cuantia || undefined,
          description: data.description || '',
        })
      })
      .catch(() => setError('Error al cargar el caso'))
      .finally(() => setIsFetching(false))
  }, [caseId])

  const set = (key: keyof CaseCreate, value: string | number | undefined) =>
    setForm((prev) => ({ ...prev, [key]: value }))

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)
    try {
      const payload: CaseCreate = {
        ...form,
        demandado: form.demandado || undefined,
        radicado: form.radicado || undefined,
        juzgado: form.juzgado || undefined,
        description: form.description || undefined,
      }

      if (isEditing && caseId) {
        await casesApi.update(Number(caseId), payload)
        navigate(`/cases/${caseId}`)
      } else {
        const { data } = await casesApi.create(payload)
        navigate(`/cases/${data.id}`)
      }
    } catch (err: unknown) {
      setError(
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
          (isEditing ? 'Error al actualizar el caso' : 'Error al crear el caso')
      )
    } finally {
      setIsLoading(false)
    }
  }

  if (isFetching) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-blue-600 dark:border-blue-400 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 p-8">
      <div className="max-w-2xl mx-auto">
        <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 mb-6 transition">
          <ArrowLeft className="w-4 h-4" /> Volver
        </button>

        <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-8 shadow-sm">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">{isEditing ? 'Editar caso' : 'Nuevo caso'}</h1>

          {error && (
            <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-300 text-sm">{error}</div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Cliente *</label>
                <input
                  required
                  value={form.cliente}
                  onChange={(e) => set('cliente', e.target.value)}
                  placeholder="Nombre del cliente o demandante"
                  className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none placeholder-gray-400 dark:placeholder-gray-500"
                />
              </div>

              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Demandado</label>
                <input
                  value={form.demandado}
                  onChange={(e) => set('demandado', e.target.value)}
                  placeholder="Nombre del demandado (opcional)"
                  className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none placeholder-gray-400 dark:placeholder-gray-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Área del derecho *</label>
                <select
                  value={form.area}
                  onChange={(e) => set('area', e.target.value as LegalArea)}
                  className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                >
                  {AREAS.map((a) => (
                    <option key={a.value} value={a.value}>{a.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Radicado</label>
                <input
                  value={form.radicado}
                  onChange={(e) => set('radicado', e.target.value)}
                  placeholder="11001-31-03-001-2024-00001"
                  className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none placeholder-gray-400 dark:placeholder-gray-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Juzgado</label>
                <input
                  value={form.juzgado}
                  onChange={(e) => set('juzgado', e.target.value)}
                  placeholder="Juzgado Civil del Circuito"
                  className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none placeholder-gray-400 dark:placeholder-gray-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Cuant\u00eda (COP)</label>
                <input
                  type="number"
                  value={form.cuantia ?? ''}
                  onChange={(e) => set('cuantia', e.target.value ? Number(e.target.value) : undefined)}
                  placeholder="50000000"
                  className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none placeholder-gray-400 dark:placeholder-gray-500"
                />
              </div>

              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Descripci\u00f3n</label>
                <textarea
                  rows={3}
                  value={form.description}
                  onChange={(e) => set('description', e.target.value)}
                  placeholder="Resumen breve del caso..."
                  className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none resize-none placeholder-gray-400 dark:placeholder-gray-500"
                />
              </div>
            </div>

            <div className="flex gap-3 pt-2">
              <button
                type="button"
                onClick={() => navigate(-1)}
                className="flex-1 py-2.5 border border-gray-300 dark:border-gray-700 text-gray-600 dark:text-gray-400 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={isLoading}
                className="flex-1 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition shadow-lg shadow-blue-600/20"
              >
                {isLoading ? 'Guardando...' : isEditing ? 'Guardar cambios' : 'Crear caso'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
