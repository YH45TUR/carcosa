import { Routes, Route, Navigate } from 'react-router-dom'
import { LoginForm } from './components/Auth/LoginForm'
import { ProtectedRoute } from './components/Auth/ProtectedRoute'
import { CaseList } from './components/Cases/CaseList'
import { CaseDetail } from './components/Cases/CaseDetail'
import { CaseForm } from './components/Cases/CaseForm'
import { ChatWindow } from './components/Chat/ChatWindow'
import { ErrorBoundary } from './components/ui/ErrorBoundary'

function App() {
  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Routes>
          <Route path="/login" element={<LoginForm />} />
          
          <Route element={<ProtectedRoute />}>
            <Route path="/" element={<Navigate to="/cases" replace />} />
            <Route path="/cases" element={<CaseList />} />
            <Route path="/cases/new" element={<CaseForm />} />
            <Route path="/cases/:caseId" element={<CaseDetail />} />
            <Route path="/chat" element={<ChatWindow />} />
          </Route>
          
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </ErrorBoundary>
  )
}

export default App