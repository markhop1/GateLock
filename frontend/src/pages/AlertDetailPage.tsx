import { useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useNotificationStore } from '../store/notificationStore'
import { format } from 'date-fns'
import { es } from 'date-fns/locale/es'
import { ArrowLeftIcon, CheckCircleIcon, XCircleIcon, QuestionMarkCircleIcon } from '@heroicons/react/24/outline'
import { alertService } from '../services/alert.service'
import { getBackendAssetUrl } from '../services/api'

export default function AlertDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { getNotificationById, fetchNotifications } = useNotificationStore()
  const notification = id ? getNotificationById(id) : undefined

  useEffect(() => {
    // Fetch notification if not in store
    if (id && !notification) {
      alertService.getById(id).then(() => {
        fetchNotifications()
      })
    }
  }, [id, notification, fetchNotifications])

  if (!notification) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="text-center py-12">
          <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-2">
            Alerta no encontrada
          </h2>
          <Link
            to="/history"
            className="text-primary-600 hover:text-primary-700 dark:text-primary-400"
          >
            Volver al historial
          </Link>
        </div>
      </div>
    )
  }

  const getStatusIcon = () => {
    switch (notification.status) {
      case 'accepted':
        return <CheckCircleIcon className="w-6 h-6 text-green-500" />
      case 'ignored':
        return <XCircleIcon className="w-6 h-6 text-red-500" />
      case 'unanswered':
        return <QuestionMarkCircleIcon className="w-6 h-6 text-orange-500" />
      default:
        return null
    }
  }

  const getStatusText = () => {
    switch (notification.status) {
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

  return (
    <div className="max-w-4xl mx-auto">
      <Link
        to="/history"
        className="inline-flex items-center text-primary-600 hover:text-primary-700 dark:text-primary-400 mb-6"
      >
        <ArrowLeftIcon className="w-5 h-5 mr-2" />
        Volver al historial
      </Link>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Detalle de la Alerta
            </h1>
            <div className="flex items-center gap-2">
              {getStatusIcon()}
              <span className="text-lg font-medium text-gray-700 dark:text-gray-300">
                {getStatusText()}
              </span>
            </div>
          </div>
        </div>

        <div className="mb-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Persona detectada
          </h2>
          <p className="text-xl text-gray-700 dark:text-gray-300">
            {notification.personName}
          </p>
        </div>

        {notification.videoUrl && (
          <div className="mb-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Video de la solicitud — {notification.personName}
            </h2>
            <video
              src={getBackendAssetUrl(notification.videoUrl)}
              controls
              className="w-full rounded-md bg-gray-100 dark:bg-gray-700"
              style={{ maxHeight: '500px' }}
              title={`Clip de ${notification.personName}`}
            >
              Tu navegador no soporta la reproducción de video.
            </video>
          </div>
        )}

        <div className="mb-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Mensaje
          </h2>
          <p className="text-gray-700 dark:text-gray-300">{notification.message}</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              Fecha de solicitud
            </h3>
            <p className="text-gray-900 dark:text-white">
              {format(notification.timestamp, "d 'de' MMMM 'de' yyyy 'a las' HH:mm", {
                locale: es,
              })}
            </p>
          </div>
          {notification.decisionTimestamp && (
            <div>
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                Fecha de decisión
              </h3>
              <p className="text-gray-900 dark:text-white">
                {format(
                  notification.decisionTimestamp,
                  "d 'de' MMMM 'de' yyyy 'a las' HH:mm",
                  {
                    locale: es,
                  }
                )}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
