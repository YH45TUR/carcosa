// Sistema Legal CO - Virtual List Hook
// Renderiza solo los mensajes visibles + buffer para rendimiento óptimo
import { useState, useRef, useCallback, useEffect, type RefObject } from 'react'

interface UseVirtualListOptions<T> {
  items: T[]
  itemHeight: number
  overscan?: number
  containerRef: RefObject<HTMLDivElement | null>
}

interface UseVirtualListResult<T> {
  visibleItems: T[]
  totalHeight: number
  offsetY: number
  isNearBottom: boolean
  scrollToBottom: () => void
  handleScroll: () => void
}

export function useVirtualList<T>({
  items,
  itemHeight = 80,
  overscan = 5,
  containerRef,
}: UseVirtualListOptions<T>): UseVirtualListResult<T> {
  const [scrollTop, setScrollTop] = useState(0)
  const [containerHeight, setContainerHeight] = useState(0)
  const [isNearBottom, setIsNearBottom] = useState(true)
  const rafRef = useRef<number | null>(null)

  const totalHeight = items.length * itemHeight

  // Observar cambios de tamaño del contenedor
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setContainerHeight(entry.contentRect.height)
      }
    })
    observer.observe(container)
    setContainerHeight(container.clientHeight)

    return () => observer.disconnect()
  }, [containerRef])

  // Scroll suave al final cuando hay nuevos mensajes
  const scrollToBottom = useCallback(() => {
    const container = containerRef.current
    if (!container) return
    container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' })
  }, [containerRef])

  // Detectar si el usuario está cerca del final
  const checkNearBottom = useCallback(() => {
    const container = containerRef.current
    if (!container) return

    const threshold = 150
    const near = container.scrollHeight - container.scrollTop - container.clientHeight < threshold
    setIsNearBottom(near)
  }, [containerRef])

  // Scroll automático cuando hay nuevos mensajes si está cerca del final
  useEffect(() => {
    if (isNearBottom && items.length > 0) {
      scrollToBottom()
    }
  }, [items.length, isNearBottom, scrollToBottom])

  const handleScroll = useCallback(() => {
    if (rafRef.current) return

    rafRef.current = requestAnimationFrame(() => {
      const container = containerRef.current
      if (container) {
        setScrollTop(container.scrollTop)
        checkNearBottom()
      }
      rafRef.current = null
    })
  }, [containerRef, checkNearBottom])

  // Calcular qué items son visibles
  const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan)
  const endIndex = Math.min(
    items.length,
    Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
  )

  const visibleItems = items.slice(startIndex, endIndex)
  const offsetY = startIndex * itemHeight

  return {
    visibleItems,
    totalHeight,
    offsetY,
    isNearBottom,
    scrollToBottom,
    handleScroll,
  }
}
