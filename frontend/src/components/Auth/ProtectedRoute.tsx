import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'

export function ProtectedRoute() {
  const { user, accessToken } = useAuth()

  if (!user || !accessToken) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
