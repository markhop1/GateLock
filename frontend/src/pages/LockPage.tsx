import { useEffect, useState } from 'react'
import {
  LockClosedIcon,
  LockOpenIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline'
import { nukiService, type LockStatus } from '../services/nuki.service'

const LABELS: Record<LockStatus, string> = {
  locked: 'Cerrado',
  unlocked: 'Abierto',
  unlatched: 'Pestillo abierto',
  unavailable: 'No disponible',
  unknown: 'Estado desconocido',
}

export default function LockPage() {
  const [lockStatus, setLockStatus] = useState<Awaited<ReturnType<typeof nukiService.getStatus>> | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<'lock' | 'unlock' | null>(null)
  const [error, setError] = useState<string | null>(null)

  const fetchStatus = async () => {
    try {
      setError(null)
      const status = await nukiService.getStatus()
      setLockStatus(status)
    } catch (err) {
      setError('No se ha podido obtener el estado del candado')
      setLockStatus({ configured: true, status: 'unavailable', error: true })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStatus()
  }, [])

  const handleLock = async () => {
    try {
      setActionLoading('lock')
      setError(null)
      await nukiService.lock()
      setLockStatus((prev) =>
        prev && prev.configured === true ? { ...prev, status: 'locked' as const } : prev
      )
      setTimeout(fetchStatus, 2500)
    } catch {
      setError('No se ha podido cerrar el candado')
    } finally {
      setActionLoading(null)
    }
  }

  const handleUnlock = async () => {
    try {
      setActionLoading('unlock')
      setError(null)
      await nukiService.unlock()
      setLockStatus((prev) =>
        prev && prev.configured === true ? { ...prev, status: 'unlocked' as const } : prev
      )
      setTimeout(fetchStatus, 2500)
    } catch {
      setError('No se ha podido abrir el candado')
    } finally {
      setActionLoading(null)
    }
  }

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto flex items-center justify-center py-24">
        <ArrowPathIcon className="w-12 h-12 text-primary-500 animate-spin" />
      </div>
    )
  }

  const notConfigured = lockStatus?.configured === false
  const canControl =
    lockStatus?.configured === true &&
    lockStatus.status !== 'unavailable' &&
    lockStatus.status !== 'unknown'

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Candado
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Abre o cierra el candado desde la aplicación
        </p>
      </div>

      {notConfigured && (
        <div className="p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg mb-6">
          <p className="text-sm text-amber-800 dark:text-amber-300 flex items-center gap-2">
            <ExclamationTriangleIcon className="w-5 h-5 shrink-0" />
            <span>
              Candado no configurado. Configura NUKI_TOKEN y NUKI_SMARTLOCK_ID en
              el backend.
            </span>
          </p>
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg mb-6">
          <p className="text-sm text-red-800 dark:text-red-300 flex items-center gap-2">
            <ExclamationTriangleIcon className="w-5 h-5 shrink-0" />
            {error}
          </p>
        </div>
      )}

      {canControl && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex flex-col items-center gap-6">
            <div
              className={`flex items-center gap-3 px-4 py-2 rounded-lg text-lg font-medium ${
                lockStatus!.status === 'unlocked' || lockStatus!.status === 'unlatched'
                  ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
                  : 'bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-300'
              }`}
            >
              {lockStatus!.status === 'unlocked' || lockStatus!.status === 'unlatched' ? (
                <LockOpenIcon className="w-8 h-8" />
              ) : (
                <LockClosedIcon className="w-8 h-8" />
              )}
              {lockStatus!.name && <span>{lockStatus!.name}: </span>}
              <span>{LABELS[lockStatus!.status]}</span>
            </div>

            <div className="flex gap-4">
              <button
                onClick={handleUnlock}
                disabled={actionLoading !== null}
                className="flex items-center gap-2 bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white font-medium py-3 px-6 rounded-lg transition-colors"
              >
                {actionLoading === 'unlock' ? (
                  <ArrowPathIcon className="w-5 h-5 animate-spin" />
                ) : (
                  <LockOpenIcon className="w-5 h-5" />
                )}
                Abrir
              </button>
              <button
                onClick={handleLock}
                disabled={actionLoading !== null}
                className="flex items-center gap-2 bg-amber-600 hover:bg-amber-700 disabled:bg-amber-400 text-white font-medium py-3 px-6 rounded-lg transition-colors"
              >
                {actionLoading === 'lock' ? (
                  <ArrowPathIcon className="w-5 h-5 animate-spin" />
                ) : (
                  <LockClosedIcon className="w-5 h-5" />
                )}
                Cerrar
              </button>
            </div>

            <button
              onClick={fetchStatus}
              disabled={loading}
              className="text-sm text-gray-500 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 flex items-center gap-1"
            >
              <ArrowPathIcon className="w-4 h-4" />
              Actualizar estado
            </button>
          </div>
        </div>
      )}

      {lockStatus?.configured === true &&
        (lockStatus.status === 'unavailable' || lockStatus.status === 'unknown') && (
          <div className="p-4 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg">
            <p className="text-sm text-orange-800 dark:text-orange-300">
              No se ha podido obtener el estado del candado. Comprueba la conexión con Nuki Web.
            </p>
            <button
              onClick={fetchStatus}
              className="mt-2 text-sm text-orange-700 dark:text-orange-200 underline"
            >
              Reintentar
            </button>
          </div>
        )}
    </div>
  )
}
