import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import { useQuickLogin } from './hooks/useQuickLogin'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import MainLayout from './layouts/MainLayout'
import HomePage from './pages/HomePage'
import HistoryPage from './pages/HistoryPage'
import AddPersonPage from './pages/AddPersonPage'
import LockPage from './pages/LockPage'
import SettingsPage from './pages/SettingsPage'
import AlertDetailPage from './pages/AlertDetailPage'

function App() {
  const { isAuthenticated, checkAuth } = useAuthStore()
  
  // Enable quick login with Ctrl+Shift+K
  useQuickLogin()

  useEffect(() => {
    // Check if user is authenticated on app load
    if (localStorage.getItem('auth-storage')) {
      checkAuth()
    }
  }, [checkAuth])

  return (
    <Routes>
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />}
      />
      <Route
        path="/register"
        element={isAuthenticated ? <Navigate to="/" replace /> : <RegisterPage />}
      />
      <Route
        path="/"
        element={
          isAuthenticated ? (
            <MainLayout>
              <HomePage />
            </MainLayout>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      <Route
        path="/history"
        element={
          isAuthenticated ? (
            <MainLayout>
              <HistoryPage />
            </MainLayout>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      <Route
        path="/history/:id"
        element={
          isAuthenticated ? (
            <MainLayout>
              <AlertDetailPage />
            </MainLayout>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      <Route
        path="/access"
        element={
          isAuthenticated ? (
            <MainLayout>
              <AddPersonPage />
            </MainLayout>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      <Route
        path="/lock"
        element={
          isAuthenticated ? (
            <MainLayout>
              <LockPage />
            </MainLayout>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      <Route
        path="/settings"
        element={
          isAuthenticated ? (
            <MainLayout>
              <SettingsPage />
            </MainLayout>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
    </Routes>
  )
}

export default App
