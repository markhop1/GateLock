import { useState, useEffect } from 'react'
import { usePersonStore } from '../store/personStore'
import { useNotificationStore } from '../store/notificationStore'
import {
  UserPlusIcon,
  CheckCircleIcon,
  PencilIcon,
  TrashIcon,
  XMarkIcon,
  UserIcon,
  CheckIcon,
} from '@heroicons/react/24/outline'
import { format } from 'date-fns'

export default function AddPersonPage() {
  const {
    persons,
    loading,
    error,
    addPerson,
    updatePerson,
    deletePerson,
    fetchPersons,
  } = usePersonStore()
  const { fetchNotifications } = useNotificationStore()

  const [editingId, setEditingId] = useState<string | null>(null)
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [newName, setNewName] = useState('')
  const [editingName, setEditingName] = useState('')
  const [success, setSuccess] = useState(false)
  const [formError, setFormError] = useState('')

  // Fetch persons on mount
  useEffect(() => {
    fetchPersons()
  }, [fetchPersons])

  const handleAddPerson = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError('')

    if (!newName.trim()) {
      setFormError('El nombre es obligatorio')
      return
    }

    try {
      await addPerson({
        name: newName.trim(),
      })
      setNewName('')
      setShowAddForm(false)
      setSuccess(true)
      setTimeout(() => setSuccess(false), 3000)
    } catch (err: any) {
      setFormError(err.response?.data?.error || 'Error al añadir la persona')
    }
  }

  const startEditing = (person: typeof persons[0]) => {
    setEditingId(person.id)
    setEditingName(person.name)
    setFormError('')
    setShowAddForm(false)
  }

  const cancelEditing = () => {
    setEditingId(null)
    setEditingName('')
    setFormError('')
  }

  const handleUpdateName = async (id: string) => {
    if (!editingName.trim()) {
      setFormError('El nombre es obligatorio')
      return
    }

    try {
      await updatePerson(id, {
        name: editingName.trim(),
      })
      setEditingId(null)
      setEditingName('')
      setSuccess(true)
      // Refresh notifications to update names in history
      await fetchNotifications()
      setTimeout(() => setSuccess(false), 2000)
    } catch (err: any) {
      setFormError(err.response?.data?.error || 'Error al actualizar la persona')
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await deletePerson(id)
      setDeleteConfirmId(null)
      setSuccess(true)
      setTimeout(() => setSuccess(false), 2000)
    } catch (err: any) {
      setFormError(err.response?.data?.error || 'Error al eliminar la persona')
      setDeleteConfirmId(null)
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Gestión de Acceso
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Administra las personas con acceso al sistema
          </p>
        </div>
        {!showAddForm && !editingId && (
          <button
            onClick={() => {
              setShowAddForm(true)
              setNewName('')
              setFormError('')
            }}
            className="bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-4 rounded-md transition-colors flex items-center gap-2"
          >
            <UserPlusIcon className="w-5 h-5" />
            Añadir Persona
          </button>
        )}
      </div>

      {error && (
        <div className="mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-md">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-400 px-4 py-3 rounded-md flex items-center gap-2">
          <CheckCircleIcon className="w-5 h-5" />
          <span>Operación completada correctamente</span>
        </div>
      )}

      {/* Add Person Form */}
      {showAddForm && (
        <div className="mb-6 bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Añadir Nueva Persona
            </h2>
            <button
              onClick={() => {
                setShowAddForm(false)
                setNewName('')
                setFormError('')
              }}
              className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              <XMarkIcon className="w-6 h-6" />
            </button>
          </div>

          {formError && (
            <div className="mb-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-md">
              {formError}
            </div>
          )}

          <form onSubmit={handleAddPerson} className="flex gap-4">
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Nombre de la persona"
              required
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
              autoFocus
            />
            <button
              type="submit"
              disabled={loading}
              className="bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-4 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <CheckIcon className="w-5 h-5" />
              Añadir
            </button>
            <button
              type="button"
              onClick={() => {
                setShowAddForm(false)
                setNewName('')
                setFormError('')
              }}
              className="bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 font-medium py-2 px-4 rounded-md transition-colors"
            >
              Cancelar
            </button>
          </form>
        </div>
      )}

      {/* Persons List */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md border border-gray-200 dark:border-gray-700">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Personas Registradas ({persons.length})
          </h2>
        </div>

        {loading && !persons.length ? (
          <div className="p-12 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">
              Cargando personas...
            </p>
          </div>
        ) : persons.length === 0 ? (
          <div className="p-12 text-center">
            <UserIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">
              No hay personas registradas
            </h3>
            <p className="text-gray-500 dark:text-gray-400 mb-4">
              Añade tu primera persona para comenzar
            </p>
            <button
              onClick={() => {
                setShowAddForm(true)
                setNewName('')
                setFormError('')
              }}
              className="bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-4 rounded-md transition-colors inline-flex items-center gap-2"
            >
              <UserPlusIcon className="w-5 h-5" />
              Añadir Primera Persona
            </button>
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {persons.map((person) => (
              <div
                key={person.id}
                className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4 flex-1">
                    {/* Avatar */}
                    {person.photoUrl ? (
                      <img
                        src={person.photoUrl}
                        alt={person.name}
                        className="w-12 h-12 rounded-full object-cover"
                        onError={(e) => {
                          ;(e.target as HTMLImageElement).style.display = 'none'
                        }}
                      />
                    ) : (
                      <div className="w-12 h-12 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center flex-shrink-0">
                        <UserIcon className="w-6 h-6 text-primary-600 dark:text-primary-400" />
                      </div>
                    )}

                    {/* Name editing or display */}
                    {editingId === person.id ? (
                      <div className="flex items-center gap-2 flex-1">
                        <input
                          type="text"
                          value={editingName}
                          onChange={(e) => setEditingName(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              handleUpdateName(person.id)
                            } else if (e.key === 'Escape') {
                              cancelEditing()
                            }
                          }}
                          className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                          autoFocus
                        />
                        {formError && editingId === person.id && (
                          <span className="text-sm text-red-600 dark:text-red-400">
                            {formError}
                          </span>
                        )}
                      </div>
                    ) : (
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                          {person.name}
                        </h3>
                        {person.email && (
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {person.email}
                          </p>
                        )}
                        <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                          Añadida el {format(person.createdAt, 'dd/MM/yyyy')}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 ml-4">
                    {editingId === person.id ? (
                      <>
                        <button
                          onClick={() => handleUpdateName(person.id)}
                          disabled={loading}
                          className="p-2 text-green-600 hover:text-green-700 dark:text-green-400 dark:hover:text-green-300 transition-colors disabled:opacity-50"
                          title="Guardar cambios"
                        >
                          <CheckIcon className="w-5 h-5" />
                        </button>
                        <button
                          onClick={cancelEditing}
                          className="p-2 text-gray-600 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
                          title="Cancelar"
                        >
                          <XMarkIcon className="w-5 h-5" />
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          onClick={() => startEditing(person)}
                          className="p-2 text-gray-600 hover:text-primary-600 dark:text-gray-400 dark:hover:text-primary-400 transition-colors"
                          title="Editar nombre"
                        >
                          <PencilIcon className="w-5 h-5" />
                        </button>
                        <button
                          onClick={() => setDeleteConfirmId(person.id)}
                          className="p-2 text-gray-600 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400 transition-colors"
                          title="Eliminar persona"
                        >
                          <TrashIcon className="w-5 h-5" />
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {deleteConfirmId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Confirmar eliminación
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              ¿Estás seguro de que quieres eliminar a{' '}
              <strong>
                {persons.find((p) => p.id === deleteConfirmId)?.name}
              </strong>
              ? Esta acción no se puede deshacer.
            </p>
            <div className="flex gap-4">
              <button
                onClick={() => handleDelete(deleteConfirmId)}
                disabled={loading}
                className="flex-1 bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Eliminando...' : 'Eliminar'}
              </button>
              <button
                onClick={() => setDeleteConfirmId(null)}
                className="flex-1 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 font-medium py-2 px-4 rounded-md transition-colors"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
