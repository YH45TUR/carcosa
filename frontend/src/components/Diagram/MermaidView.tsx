// Sistema Legal CO - Mermaid Diagram View
import { useEffect, useRef, useState } from 'react'
import mermaid from 'mermaid'
import { Download, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react'

interface Props {
  chart: string
  title?: string
  diagramType?: 'timeline' | 'flowchart' | 'graph'
}

mermaid.initialize({
  theme: 'base',
  themeVariables: {
    primaryColor: '#0ea5e9',
    primaryTextColor: '#1e293b',
    primaryBorderColor: '#0284c7',
    lineColor: '#94a3b8',
    secondaryColor: '#f1f5f9',
    tertiaryColor: '#ffffff',
    fontSize: '14px',
  },
  securityLevel: 'loose',
})

export function MermaidView({ chart, title }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [svg, setSvg] = useState<string>('')
  const [zoom, setZoom] = useState(1)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const renderDiagram = async () => {
      if (!chart) return

      try {
        setError(null)
        const id = `mermaid-${Date.now()}`
        const { svg: renderedSvg } = await mermaid.render(id, chart)
        setSvg(renderedSvg)
      } catch (err: any) {
        setError(err.message || 'Error al renderizar diagrama')
      }
    }

    renderDiagram()
  }, [chart])

  const handleExportPNG = () => {
    if (!containerRef.current) return
    const svgEl = containerRef.current.querySelector('svg')
    if (!svgEl) return

    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    const svgData = new XMLSerializer().serializeToString(svgEl)
    const img = new Image()

    img.onload = () => {
      canvas.width = img.width * 2
      canvas.height = img.height * 2
      ctx?.scale(2, 2)
      ctx?.drawImage(img, 0, 0)

      const link = document.createElement('a')
      link.download = `${title || 'diagrama'}.png`
      link.href = canvas.toDataURL('image/png')
      link.click()
    }

    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)))
  }

  const handleExportSVG = () => {
    if (!containerRef.current) return
    const svgEl = containerRef.current.querySelector('svg')
    if (!svgEl) return

    const svgData = new XMLSerializer().serializeToString(svgEl)
    const blob = new Blob([svgData], { type: 'image/svg+xml' })
    const url = URL.createObjectURL(blob)

    const link = document.createElement('a')
    link.download = `${title || 'diagrama'}.svg`
    link.href = url
    link.click()
    URL.revokeObjectURL(url)
  }

  if (error) {
    return (
      <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-6 text-center">
        <p className="text-yellow-700 dark:text-yellow-300 text-sm">
          Error al renderizar diagrama: {error}
        </p>
      </div>
    )
  }

  if (!chart) {
    return (
      <div className="bg-gray-50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-700 rounded-xl p-12 text-center">
        <p className="text-gray-500 dark:text-gray-400 text-sm">
          No hay diagrama para mostrar
        </p>
      </div>
    )
  }

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden ${
      isFullscreen ? 'fixed inset-4 z-50 shadow-2xl' : ''
    }`}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
        <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">
          {title || 'Diagrama Legal'}
        </h3>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setZoom(z => Math.max(0.25, z - 0.25))}
            className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
            title="Alejar"
          >
            <ZoomOut className="w-4 h-4 text-gray-500" />
          </button>
          <span className="text-xs text-gray-500 min-w-[3rem] text-center">
            {Math.round(zoom * 100)}%
          </span>
          <button
            onClick={() => setZoom(z => Math.min(3, z + 0.25))}
            className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
            title="Acercar"
          >
            <ZoomIn className="w-4 h-4 text-gray-500" />
          </button>
          <div className="w-px h-6 bg-gray-300 dark:bg-gray-600 mx-1" />
          <button
            onClick={handleExportPNG}
            className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
            title="Exportar PNG"
          >
            <Download className="w-4 h-4 text-gray-500" />
          </button>
          <button
            onClick={handleExportSVG}
            className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
            title="Exportar SVG"
          >
            <Download className="w-4 h-4 text-gray-500" />
          </button>
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
            title="Pantalla completa"
          >
            <Maximize2 className="w-4 h-4 text-gray-500" />
          </button>
        </div>
      </div>

      {/* Diagram */}
      <div
        ref={containerRef}
        className="p-6 overflow-auto flex justify-center"
        style={{ transform: `scale(${zoom})`, transformOrigin: 'top center' }}
        dangerouslySetInnerHTML={{ __html: svg }}
      />
    </div>
  )
}
