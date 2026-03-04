import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useNotificationStore } from '../store/notificationStore'
import { format } from 'date-fns'
import { es } from 'date-fns/locale/es'
import { ClockIcon, CheckCircleIcon, XCircleIcon, QuestionMarkCircleIcon } from '@heroicons/react/24/outline'

export default function HistoryPage() {
  const { notifications, fetchNotifications } = useNotificationStore()

  useEffect(() => {
    fetchNotifications()
  }, [fetchNotifications])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'accepted':
        return <CheckCircleIcon className="w-5 h-5 text-primary-500" />
      case 'ignored':
        return <XCircleIcon className="w-5 h-5 text-red-500" />
      case 'unanswered':
        return <QuestionMarkCircleIcon className="w-5 h-5 text-orange-500" />
      default:
        return null
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'accepted':
        return 'Aceptada'
      case 'ignored':
        return 'Ignorada'
      case 'unanswered':
        return 'No respondida'
      default:
        return 'Pendiente'
    }
  }

  const sortedNotifications = [...notifications].sort(
    (a, b) => b.timestamp.getTime() - a.timestamp.getTime()
  )

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Historial de Alertas
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Todas las solicitudes de acceso registradas
        </p>
      </div>

      {sortedNotifications.length === 0 ? (
        <div className="text-center py-12">
          <ClockIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-2">
            No hay alertas registradas
          </h2>
          <p className="text-gray-500 dark:text-gray-400">
            El historial aparecerá aquí cuando haya solicitudes de acceso
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {sortedNotifications.map((notification) => (
            <Link
              key={notification.id}
              to={`/history/${notification.id}`}
              className="block bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 border border-gray-200 dark:border-gray-700 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                    {notification.personName}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {format(notification.timestamp, "d 'de' MMMM 'a las' HH:mm", {
                      locale: es,
                    })}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {getStatusIcon(notification.status)}
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {getStatusText(notification.status)}
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
