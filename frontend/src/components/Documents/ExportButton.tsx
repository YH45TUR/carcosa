// Sistema Legal CO - Export Button
import { useState, useRef, useEffect } from 'react'
import { FileDown, FileText, File as FilePdf } from 'lucide-react'

interface Props {
  onExport?: (format: 'docx' | 'pdf') => void
  isLoading?: boolean
}

export function ExportButton({ onExport, isLoading }: Props) {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleExport = (format: 'docx' | 'pdf') => {
    setIsOpen(false)
    onExport?.(format)
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isLoading}
        className="inline-flex items-center gap-2 px-4 py-2.5 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 transition-colors font-medium text-sm"
      >
        <FileDown className="w-4 h-4" />
        Exportar
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 py-2 z-50">
          <button
            onClick={() => handleExport('docx')}
            className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <FileText className="w-4 h-4 text-blue-600" />
            <div className="text-left">
              <p className="font-medium">Word (.docx)</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Formato NTC 1486</p>
            </div>
          </button>
          <button
            onClick={() => handleExport('pdf')}
            className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <FilePdf className="w-4 h-4 text-red-600" />
            <div className="text-left">
              <p className="font-medium">PDF</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Exportación con estilos</p>
            </div>
          </button>
        </div>
      )}
    </div>
  )
}
