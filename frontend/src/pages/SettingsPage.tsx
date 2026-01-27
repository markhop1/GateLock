import { useAuthStore } from '../store/authStore'
import { useNavigate } from 'react-router-dom'
import { ArrowRightOnRectangleIcon, UserIcon } from '@heroicons/react/24/outline'

export default function SettingsPage() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Ajustes
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Gestiona tu cuenta y preferencias
        </p>
      </div>

      <div className="space-y-4">
        {/* User Info Card */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center">
              <UserIcon className="w-6 h-6 text-primary-600 dark:text-primary-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Información de la cuenta
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Detalles de tu cuenta
              </p>
            </div>
          </div>
          <div className="space-y-2">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Nombre</p>
              <p className="text-gray-900 dark:text-white font-medium">
                {user?.name || 'No disponible'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Email</p>
              <p className="text-gray-900 dark:text-white font-medium">
                {user?.email || 'No disponible'}
              </p>
            </div>
          </div>
        </div>

        {/* Logout Card */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                Cerrar sesión
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Salir de tu cuenta de GateLock
              </p>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
            >
              <ArrowRightOnRectangleIcon className="w-5 h-5" />
              Cerrar sesión
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
