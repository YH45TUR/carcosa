// Sistema Legal CO - File Upload
import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, X, AlertCircle, CheckCircle, Loader2 } from 'lucide-react'
import { api } from '../../services/api'
import type { Document } from '../../types'

interface Props {
  caseId: number
  onUploaded?: (doc: Document) => void
}

interface UploadingFile {
  file: File
  progress: number
  status: 'pending' | 'uploading' | 'processing' | 'done' | 'error'
  error?: string
  docId?: number
}

const ACCEPTED_TYPES = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'image/png': ['.png'],
  'image/jpeg': ['.jpg', '.jpeg'],
}

const MAX_SIZE = 50 * 1024 * 1024 // 50MB

export function FileUpload({ caseId, onUploaded }: Props) {
  const [files, setFiles] = useState<UploadingFile[]>([])

  const uploadFile = useCallback(async (file: File, idx: number) => {
    const formData = new FormData()
    formData.append('file', file)

    setFiles(prev => prev.map((f, i) => i === idx ? { ...f, status: 'uploading', progress: 10 } : f))

    try {
      const { data } = await api.post<Document & { message: string }>(
        `/api/documents/upload/${caseId}`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (e) => {
            const pct = Math.round((e.loaded * 80) / (e.total ?? 1))
            setFiles(prev => prev.map((f, i) => i === idx ? { ...f, progress: pct } : f))
          },
        }
      )

      // Archivo subido — ahora esperar procesamiento si hay job_id
      setFiles(prev => prev.map((f, i) =>
        i === idx
          ? { ...f, status: 'processing', progress: 85, docId: data.id }
          : f
      ))

      // Polling de status si el procesamiento es async
      if (data.has_text === false && data.job_id) {
        let attempts = 0
        const poll = setInterval(async () => {
          attempts++
          try {
            const { data: updated } = await api.get<Document>(`/api/documents/${data.id}`)
            if (updated.has_text || attempts > 30) {
              clearInterval(poll)
              setFiles(prev => prev.map((f, i) =>
                i === idx ? { ...f, status: 'done', progress: 100 } : f
              ))
              onUploaded?.(updated)
            }
          } catch {
            clearInterval(poll)
          }
        }, 2000)
      } else {
        setFiles(prev => prev.map((f, i) =>
          i === idx ? { ...f, status: 'done', progress: 100 } : f
        ))
        onUploaded?.(data)
      }
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Error al subir archivo'
      setFiles(prev => prev.map((f, i) =>
        i === idx ? { ...f, status: 'error', error: msg } : f
      ))
    }
  }, [caseId, onUploaded])

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const startIdx = files.length
    const newFiles = acceptedFiles.map(file => ({
      file, progress: 0, status: 'pending' as const,
    }))
    setFiles(prev => [...prev, ...newFiles])
    acceptedFiles.forEach((file, i) => uploadFile(file, startIdx + i))
  }, [files.length, uploadFile])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxSize: MAX_SIZE,
    onDropRejected: (rejections) => {
      const newErrors = rejections.map(r => ({
        file: r.file, progress: 0, status: 'error' as const,
        error: r.errors[0]?.message || 'Archivo inválido',
      }))
      setFiles(prev => [...prev, ...newErrors])
    },
  })

  const removeFile = (index: number) => setFiles(prev => prev.filter((_, i) => i !== index))

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const statusLabel = (s: UploadingFile['status']) => ({
    pending: 'Pendiente',
    uploading: 'Subiendo...',
    processing: 'Procesando (OCR/NER)...',
    done: 'Listo',
    error: 'Error',
  })[s]

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-blue-400'
        }`}
      >
        <input {...getInputProps()} />
        <Upload className={`w-10 h-10 mx-auto mb-3 ${isDragActive ? 'text-blue-500' : 'text-gray-400'}`} />
        <p className="text-sm text-gray-600">
          {isDragActive ? 'Suelta los archivos aquí...' : 'Arrastra y suelta archivos, o haz clic para seleccionar'}
        </p>
        <p className="text-xs text-gray-500 mt-1">PDF, DOCX, PNG, JPG · Máximo 50 MB</p>
      </div>

      {files.length > 0 && (
        <div className="space-y-2">
          {files.map((f, idx) => (
            <div
              key={idx}
              className={`flex items-center gap-3 p-3 rounded-lg border ${
                f.status === 'error'
                  ? 'border-red-200 bg-red-50'
                  : f.status === 'done'
                  ? 'border-green-200 bg-green-50'
                  : 'border-gray-200 bg-white'
              }`}
            >
              <FileText className="w-5 h-5 shrink-0 text-gray-400" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{f.file.name}</p>
                <p className="text-xs text-gray-500">{formatSize(f.file.size)} · {statusLabel(f.status)}</p>
                {(f.status === 'uploading' || f.status === 'processing') && (
                  <div className="mt-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full transition-all duration-300"
                      style={{ width: `${f.progress}%` }}
                    />
                  </div>
                )}
                {f.error && <p className="text-xs text-red-600 mt-0.5">{f.error}</p>}
              </div>
              {f.status === 'done' ? (
                <CheckCircle className="w-5 h-5 text-green-500 shrink-0" />
              ) : f.status === 'error' ? (
                <AlertCircle className="w-5 h-5 text-red-500 shrink-0" />
              ) : f.status === 'uploading' || f.status === 'processing' ? (
                <Loader2 className="w-5 h-5 text-blue-500 animate-spin shrink-0" />
              ) : (
                <button onClick={() => removeFile(idx)} className="p-1 hover:bg-gray-100 rounded transition">
                  <X className="w-4 h-4 text-gray-400" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
