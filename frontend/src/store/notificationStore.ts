import { create } from 'zustand'
import { alertService, Alert } from '../services/alert.service'
import { getErrorMessage } from '../types/error'

export type NotificationStatus = 'pending' | 'accepted' | 'ignored' | 'unanswered'

export interface Notification {
  id: string
  personId: string
  personName: string
  videoUrl: string
  message: string
  status: NotificationStatus
  timestamp: Date
  decisionTimestamp?: Date
}

// Helper to convert Alert to Notification
const alertToNotification = (alert: Alert): Notification => ({
  ...alert,
  timestamp: new Date(alert.timestamp),
  decisionTimestamp: alert.decisionTimestamp ? new Date(alert.decisionTimestamp) : undefined,
})

interface NotificationState {
  notifications: Notification[]
  loading: boolean
  error: string | null
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => Promise<void>
  updateNotificationStatus: (id: string, status: NotificationStatus) => Promise<void>
  getNotificationById: (id: string) => Notification | undefined
  fetchNotifications: (status?: NotificationStatus) => Promise<void>
  clearNotifications: () => void
  checkExpiredNotifications: () => void
}

const EXPIRATION_TIME_MS = 5 * 60 * 1000 // 5 minutos en milisegundos

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],
  loading: false,
  error: null,
  addNotification: async (notification) => {
    try {
      set({ loading: true, error: null })
      const alert = await alertService.create({
        personId: notification.personId,
        personName: notification.personName,
        videoUrl: notification.videoUrl,
        message: notification.message,
      })
      const newNotification = alertToNotification(alert)
      set((state) => ({
        notifications: [newNotification, ...state.notifications],
        loading: false,
      }))
    } catch (error: unknown) {
      const errorMessage = getErrorMessage(error) || 'Error creating notification'
      console.error('Error creating notification:', error)
      set({
        error: errorMessage,
        loading: false,
      })
      throw error
    }
  },
  updateNotificationStatus: async (id, status) => {
    try {
      if (status === 'accepted' || status === 'ignored') {
        const alert = await alertService.updateStatus(id, status)
        const updatedNotification = alertToNotification(alert)
        set((state) => ({
          notifications: state.notifications.map((notif) =>
            notif.id === id ? updatedNotification : notif
          ),
        }))
      } else {
        // For local state updates (unanswered)
        set((state) => ({
          notifications: state.notifications.map((notif) =>
            notif.id === id
              ? { ...notif, status, decisionTimestamp: new Date() }
              : notif
          ),
        }))
      }
    } catch (error: unknown) {
      set({
        error: getErrorMessage(error) || 'Error updating notification',
      })
      throw error
    }
  },
  getNotificationById: (id) => {
    return get().notifications.find((notif) => notif.id === id)
  },
  fetchNotifications: async (status?: NotificationStatus) => {
    try {
      set({ loading: true, error: null })
      const alerts = await alertService.getAll(status)
      const notifications = alerts.map(alertToNotification)
      set({ notifications, loading: false })
    } catch (error: unknown) {
      set({
        error: getErrorMessage(error) || 'Error fetching notifications',
        loading: false,
      })
    }
  },
  clearNotifications: () => {
    set({ notifications: [], error: null })
  },
  checkExpiredNotifications: () => {
    const now = new Date()
    set((state) => ({
      notifications: state.notifications.map((notif) => {
        if (notif.status === 'pending') {
          const timeDiff = now.getTime() - notif.timestamp.getTime()
          if (timeDiff > EXPIRATION_TIME_MS) {
            return {
              ...notif,
              status: 'unanswered' as NotificationStatus,
              decisionTimestamp: new Date(),
            }
          }
        }
        return notif
      }),
    }))
  },
}))
