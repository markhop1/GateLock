import { useEffect, useState, useRef } from 'react'
import { useNotificationStore } from '../store/notificationStore'
import NotificationCard from '../components/NotificationCard'
import { BellIcon } from '@heroicons/react/24/outline'

// Función para simular notificaciones (se puede llamar desde la consola del navegador)
declare global {
  interface Window {
    simulateNotification: (personName?: string) => void
  }
}

export default function HomePage() {
  const {
    notifications,
    addNotification,
    updateNotificationStatus,
    checkExpiredNotifications,
    fetchNotifications,
  } = useNotificationStore()
  const [pendingNotifications, setPendingNotifications] = useState(
    notifications.filter((n) => n.status === 'pending')
  )
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  // Fetch notifications on mount
  useEffect(() => {
    fetchNotifications()
  }, [fetchNotifications])

  useEffect(() => {
    setPendingNotifications(notifications.filter((n) => n.status === 'pending'))
  }, [notifications])

  // Verificar notificaciones expiradas y refrescar cada 30 segundos
  useEffect(() => {
    const checkAndRefresh = () => {
      checkExpiredNotifications()
      fetchNotifications('pending')
    }
    
    checkAndRefresh()
    intervalRef.current = setInterval(checkAndRefresh, 30000) // Verificar cada 30 segundos

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [checkExpiredNotifications, fetchNotifications])

  useEffect(() => {
    // Exponer función global para simular notificaciones
    window.simulateNotification = (personName?: string) => {
      const names = [
        'Juan Pérez',
        'María García',
        'Carlos López',
        'Ana Martínez',
        'Pedro Sánchez',
      ]
      const randomName = personName || names[Math.floor(Math.random() * names.length)]
      
      // Video de ejemplo (usando un video placeholder)
      const videoUrl =
        'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4'

      addNotification({
        personId: `person-${Date.now()}`,
        personName: randomName,
        videoUrl,
        message: `${randomName} quiere acceder, ¿permitir?`,
        status: 'pending',
      })
    }

    return () => {
      delete window.simulateNotification
    }
  }, [addNotification])

  const handleAction = async (id: string, action: 'accepted' | 'ignored') => {
    try {
      await updateNotificationStatus(id, action)
      // Refresh notifications after update
      await fetchNotifications()
    } catch (error) {
      console.error('Error updating notification:', error)
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Notificaciones
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Gestiona las solicitudes de acceso en tiempo real
        </p>
        <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md">
          <p className="text-sm text-blue-800 dark:text-blue-300">
            <strong>Tip:</strong> Abre la consola del navegador y ejecuta{' '}
            <code className="bg-blue-100 dark:bg-blue-900 px-2 py-1 rounded">
              simulateNotification()
            </code>{' '}
            para simular una notificación, o{' '}
            <code className="bg-blue-100 dark:bg-blue-900 px-2 py-1 rounded">
              simulateNotification('Nombre Persona')
            </code>{' '}
            para especificar un nombre.
          </p>
        </div>
      </div>

      {pendingNotifications.length === 0 ? (
        <div className="text-center py-12">
          <BellIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-2">
            No hay notificaciones pendientes
          </h2>
          <p className="text-gray-500 dark:text-gray-400">
            Las nuevas solicitudes de acceso aparecerán aquí
          </p>
        </div>
      ) : (
        <div>
          {pendingNotifications.map((notification) => (
            <NotificationCard
              key={notification.id}
              notification={notification}
              onAction={handleAction}
            />
          ))}
        </div>
      )}
    </div>
  )
}
