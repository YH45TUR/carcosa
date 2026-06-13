import { Routes, Route, Navigate } from 'react-router-dom'
import { LoginForm } from './components/Auth/LoginForm'
import { ProtectedRoute } from './components/Auth/ProtectedRoute'
import { CaseList } from './components/Cases/CaseList'
import { CaseDetail } from './components/Cases/CaseDetail'
import { CaseForm } from './components/Cases/CaseForm'
import { ChatWindow } from './components/Chat/ChatWindow'
import { ErrorBoundary } from './components/ui/ErrorBoundary'
import { ToastContainer } from './components/ui/ToastContainer'
import { useKeyboardShortcuts, registerDefaultShortcuts } from './hooks/useKeyboardShortcuts'
import { useNavigate } from 'react-router-dom'

function AppInner() {
  const navigate = useNavigate()

  // Registrar shortcuts globales
  useKeyboardShortcuts()

  // Activar shortcuts predefinidos
  registerDefaultShortcuts({
    onSearch: () => {
      const searchInput = document.querySelector<HTMLInputElement>('input[placeholder*="Buscar"]')
      searchInput?.focus()
    },
    onNewCase: () => navigate('/cases/new'),
    onGoHome: () => navigate('/cases'),
  })

  return (
    <>
      <ToastContainer />
      <Routes>
        <Route path="/login" element={<LoginForm />} />

        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<Navigate to="/cases" replace />} />
          <Route path="/cases" element={<CaseList />} />
          <Route path="/cases/new" element={<CaseForm />} />
          <Route path="/cases/:caseId" element={<CaseDetail />} />
          <Route path="/cases/:caseId/edit" element={<CaseForm />} />
          <Route path="/chat" element={<ChatWindow />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  )
}

function App() {
  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <AppInner />
      </div>
    </ErrorBoundary>
  )
}

export default App