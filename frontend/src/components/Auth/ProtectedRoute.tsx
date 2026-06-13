// Sistema Legal CO - Protected Route
import { useEffect } from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { Loader2 } from 'lucide-react'

export function ProtectedRoute() {
  const { isAuthenticated, isLoading, checkAuth } = useAuth()

  // Verificar autenticacion al montar el componente
  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-legal-600" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}