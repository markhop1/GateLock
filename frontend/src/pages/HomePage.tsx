import { useEffect, useState, useRef } from 'react'
import { useNotificationStore, NotificationStatus } from '../store/notificationStore'
import NotificationCard from '../components/NotificationCard'
import { nukiService, type LockStatus } from '../services/nuki.service'
import { BellIcon, LockClosedIcon, LockOpenIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'

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
  const [lockStatus, setLockStatus] = useState<import('../services/nuki.service').LockStatusResponse | null>(null)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  // Fetch notifications on mount
  useEffect(() => {
    fetchNotifications()
  }, [fetchNotifications])

  useEffect(() => {
    setPendingNotifications(notifications.filter((n) => n.status === 'pending'))
  }, [notifications])

  // Fetch lock status on mount and poll every 30 seconds
  const fetchLockStatus = async () => {
    try {
      const status = await nukiService.getStatus()
      setLockStatus(status)
    } catch {
      setLockStatus({ configured: true, status: 'unavailable', error: true })
    }
  }

  useEffect(() => {
    fetchLockStatus()
  }, [])

  // Verificar notificaciones expiradas y refrescar cada 30 segundos
  useEffect(() => {
    const checkAndRefresh = () => {
      checkExpiredNotifications()
      fetchNotifications('pending')
      fetchLockStatus()
    }

    checkAndRefresh()
    intervalRef.current = setInterval(checkAndRefresh, 30000)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [checkExpiredNotifications, fetchNotifications])

  useEffect(() => {
    // Exponer función global para simular notificaciones
    const simulateNotificationFn = (personName?: string) => {
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

    ;(
      globalThis as typeof globalThis & {
        simulateNotification?: typeof simulateNotificationFn
      }
    ).simulateNotification = simulateNotificationFn

    return () => {
      delete (
        globalThis as typeof globalThis & {
          simulateNotification?: typeof simulateNotificationFn
        }
      ).simulateNotification
    }
  }, [addNotification])

  const handleAction = async (id: string, action: NotificationStatus) => {
    if (action !== 'accepted' && action !== 'ignored') {
      return
    }
    try {
      await updateNotificationStatus(id, action)
      await fetchNotifications()
      await fetchLockStatus()
      if (action === 'accepted') {
        setTimeout(() => fetchLockStatus(), 2500)
      }
    } catch (error) {
      console.error('Error updating notification:', error)
    }
  }

  const getLockStatusDisplay = () => {
    if (!lockStatus) return null
    if (lockStatus.configured === false) return null
    if (lockStatus.status === 'unavailable' || lockStatus.status === 'unknown') return null
    const labels: Record<LockStatus, string> = {
      locked: 'Cerrado',
      unlocked: 'Abierto',
      unlatched: 'Pestillo abierto',
      unavailable: 'No disponible',
      unknown: 'Estado desconocido',
    }
    const label = labels[lockStatus.status]
    const isOpen = lockStatus.status === 'unlocked' || lockStatus.status === 'unlatched'
    return (
      <div
        className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium ${
          isOpen
            ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
            : 'bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-300'
        }`}
      >
        {isOpen ? <LockOpenIcon className="w-5 h-5" /> : <LockClosedIcon className="w-5 h-5" />}
        <span>{lockStatus.name ? `${lockStatus.name}: ` : ''}{label}</span>
        {lockStatus.batteryCritical && (
          <span className="text-red-600 dark:text-red-400" title="Batería baja">
            (Batería baja)
          </span>
        )}
      </div>
    )
  }

  const showNotConfiguredNotice = lockStatus?.configured === false
  const showConnectionNotice =
    lockStatus?.configured === true &&
    (lockStatus.status === 'unavailable' || lockStatus.status === 'unknown')

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-2">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              Notificaciones
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Gestiona las solicitudes de acceso en tiempo real
            </p>
          </div>
          {getLockStatusDisplay()}
        </div>
        {(showNotConfiguredNotice || showConnectionNotice) && (
          <div className="mt-4 space-y-3">
            {showNotConfiguredNotice && (
              <div className="p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-md">
                <p className="text-sm text-amber-800 dark:text-amber-300 flex items-center gap-2">
                  <ExclamationTriangleIcon className="w-5 h-5 shrink-0" />
                  <span>
                    <strong>Candado no configurado.</strong> Configura NUKI_TOKEN y NUKI_SMARTLOCK_ID en
                    el backend para habilitar el desbloqueo remoto desde la aplicación.
                  </span>
                </p>
              </div>
            )}
            {showConnectionNotice && (
              <div className="p-4 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-md">
                <p className="text-sm text-orange-800 dark:text-orange-300 flex items-center gap-2">
                  <ExclamationTriangleIcon className="w-5 h-5 shrink-0" />
                  <span>
                    <strong>No se ha podido obtener el estado del candado.</strong> Comprueba que el
                    candado esté conectado a Nuki Web y que las credenciales sean correctas.
                  </span>
                </p>
              </div>
            )}
          </div>
        )}
        {import.meta.env.DEV && (
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
        )}
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
