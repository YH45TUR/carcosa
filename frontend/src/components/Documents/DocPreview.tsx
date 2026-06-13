// Sistema Legal CO - Document Preview
import { useState } from 'react'
import { FileText, Download, X, Maximize2, Minimize2 } from 'lucide-react'

interface Props {
  filename: string
  content?: string
  fileType?: string
  onClose?: () => void
}

export function DocPreview({ filename, content, fileType, onClose }: Props) {
  const [isFullscreen, setIsFullscreen] = useState(false)

  const fileExtension = filename.split('.').pop()?.toLowerCase()

  const getIcon = () => {
    switch (fileExtension) {
      case 'pdf': return '📄'
      case 'docx': return '📝'
      case 'png':
      case 'jpg':
      case 'jpeg': return '🖼️'
      default: return '📁'
    }
  }

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden ${
      isFullscreen ? 'fixed inset-4 z-50 shadow-2xl' : ''
    }`}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-lg">{getIcon()}</span>
          <span className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
            {filename}
          </span>
          {fileType && (
            <span className="text-xs px-2 py-0.5 bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded-full uppercase">
              {fileType}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
            title={isFullscreen ? 'Salir de pantalla completa' : 'Pantalla completa'}
          >
            {isFullscreen ? (
              <Minimize2 className="w-4 h-4 text-gray-500" />
            ) : (
              <Maximize2 className="w-4 h-4 text-gray-500" />
            )}
          </button>
          <button className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors" title="Descargar">
            <Download className="w-4 h-4 text-gray-500" />
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              <X className="w-4 h-4 text-gray-500" />
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {content ? (
          <pre className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-sans">
            {content}
          </pre>
        ) : (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <FileText className="w-12 h-12 text-gray-300 dark:text-gray-600 mb-3" />
            <p className="text-gray-500 dark:text-gray-400 text-sm">
              Vista previa no disponible para este tipo de archivo.
            </p>
            <button className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-legal-600 text-white rounded-lg hover:bg-legal-700 transition-colors text-sm">
              <Download className="w-4 h-4" />
              Descargar archivo
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
