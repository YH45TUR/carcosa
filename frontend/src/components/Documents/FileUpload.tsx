// Sistema Legal CO - File Upload
import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, X, AlertCircle, CheckCircle } from 'lucide-react'

interface Props {
  caseId: number
}

interface UploadingFile {
  file: File
  progress: number
  status: 'pending' | 'uploading' | 'done' | 'error'
  error?: string
}

const ACCEPTED_TYPES = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'image/png': ['.png'],
  'image/jpeg': ['.jpg', '.jpeg'],
}

const MAX_SIZE = 50 * 1024 * 1024 // 50MB

export function FileUpload({ caseId }: Props) {
  const [files, setFiles] = useState<UploadingFile[]>([])

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map(file => ({
      file,
      progress: 0,
      status: 'pending' as const,
    }))
    setFiles(prev => [...prev, ...newFiles])

    // TODO: Implement actual upload via api
    // Simulated upload for now
    newFiles.forEach(async (_file, idx) => {
      setFiles(prev => prev.map((pf, i) =>
        i === files.length + idx ? { ...pf, status: 'uploading' } : pf
      ))

      // Simulate progress
      for (let p = 0; p <= 100; p += 20) {
        await new Promise(r => setTimeout(r, 200))
        setFiles(prev => prev.map((pf, i) =>
          i === files.length + idx ? { ...pf, progress: p } : pf
        ))
      }

      setFiles(prev => prev.map((pf, i) =>
        i === files.length + idx ? { ...pf, status: 'done', progress: 100 } : pf
      ))
    })
  }, [caseId, files.length])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxSize: MAX_SIZE,
    onDropRejected: (rejections) => {
      const newErrors = rejections.map(r => ({
        file: r.file,
        progress: 0,
        status: 'error' as const,
        error: r.errors[0]?.message || 'Archivo inválido',
      }))
      setFiles(prev => [...prev, ...newErrors])
    }
  })

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-legal-500 bg-legal-50 dark:bg-legal-900/20'
            : 'border-gray-300 dark:border-gray-600 hover:border-legal-400 dark:hover:border-legal-600'
        }`}
      >
        <input {...getInputProps()} />
        <Upload className={`w-10 h-10 mx-auto mb-3 ${
          isDragActive ? 'text-legal-500' : 'text-gray-400'
        }`} />
        <p className="text-sm text-gray-600 dark:text-gray-400">
          {isDragActive
            ? 'Suelta los archivos aquí...'
            : 'Arrastra y suelta archivos aquí, o haz clic para seleccionar'
          }
        </p>
        <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
          PDF, DOCX, PNG, JPG · Máximo 50MB por archivo
        </p>
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div className="space-y-2">
          {files.map((f, idx) => (
            <div
              key={idx}
              className={`flex items-center gap-3 p-3 rounded-lg border ${
                f.status === 'error'
                  ? 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20'
                  : f.status === 'done'
                  ? 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20'
                  : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800'
              }`}
            >
              <FileText className={`w-5 h-5 shrink-0 ${
                f.status === 'error' ? 'text-red-500' : 'text-gray-400'
              }`} />

              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                  {f.file.name}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {formatSize(f.file.size)}
                </p>

                {/* Progress bar */}
                {f.status === 'uploading' && (
                  <div className="mt-1 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-legal-500 rounded-full transition-all duration-300"
                      style={{ width: `${f.progress}%` }}
                    />
                  </div>
                )}
              </div>

              {/* Status icon / remove */}
              {f.status === 'done' ? (
                <CheckCircle className="w-5 h-5 text-green-500 shrink-0" />
              ) : f.status === 'error' ? (
                <div className="text-right">
                  <AlertCircle className="w-5 h-5 text-red-500 shrink-0" />
                  {f.error && (
                    <p className="text-xs text-red-600 dark:text-red-400 mt-0.5">{f.error}</p>
                  )}
                </div>
              ) : (
                <button
                  onClick={() => removeFile(idx)}
                  className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
                >
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
