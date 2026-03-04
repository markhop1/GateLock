import { Notification } from '../store/notificationStore'
import { format } from 'date-fns'
import { es } from 'date-fns/locale/es'
import { CheckCircleIcon, XCircleIcon, QuestionMarkCircleIcon } from '@heroicons/react/24/outline'
import { getBackendAssetUrl } from '../services/api'

interface NotificationCardProps {
  notification: Notification
  onAction: (id: string, action: 'accepted' | 'ignored' | 'pending' | 'unanswered') => void
  showActions?: boolean
}

export default function NotificationCard({
  notification,
  onAction,
  showActions = true,
}: NotificationCardProps) {
  const getStatusIcon = () => {
    switch (notification.status) {
      case 'accepted':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />
      case 'ignored':
        return <XCircleIcon className="w-5 h-5 text-red-500" />
      case 'unanswered':
        return <QuestionMarkCircleIcon className="w-5 h-5 text-orange-500" />
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
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 mb-4 border border-gray-200 dark:border-gray-700">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
            {notification.personName} quiere acceder
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {format(notification.timestamp, "d 'de' MMMM 'a las' HH:mm", {
              locale: es,
            })}
          </p>
        </div>
        {notification.status !== 'pending' && (
          <div className="flex items-center gap-2">
            {getStatusIcon()}
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {getStatusText()}
            </span>
          </div>
        )}
      </div>

      {notification.videoUrl && (
        <div className="mb-4">
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
            Clip: {notification.personName}
          </p>
          <video
            src={getBackendAssetUrl(notification.videoUrl)}
            controls
            className="w-full rounded-md bg-gray-100 dark:bg-gray-700"
            style={{ maxHeight: '300px' }}
            title={`Video de ${notification.personName}`}
          >
            Tu navegador no soporta la reproducción de video.
          </video>
        </div>
      )}

      <p className="text-gray-700 dark:text-gray-300 mb-4">{notification.message}</p>

      {showActions && notification.status === 'pending' && (
        <div className="flex flex-col sm:flex-row gap-2">
          <button
            onClick={() => onAction(notification.id, 'accepted')}
            className="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
          >
            Abrir
          </button>
          <button
            onClick={() => onAction(notification.id, 'ignored')}
            className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
          >
            Ignorar
          </button>
        </div>
      )}
    </div>
  )
}
