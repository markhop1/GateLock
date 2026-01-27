import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useNotificationStore } from '../notificationStore'
import { alertService, Alert } from '../../services/alert.service'

// Mock alert service
vi.mock('../../services/alert.service', () => ({
  alertService: {
    getAll: vi.fn(),
    getById: vi.fn(),
    create: vi.fn(),
    updateStatus: vi.fn(),
  },
}))

describe('Notification Store', () => {
  beforeEach(() => {
    // Reset store state
    useNotificationStore.setState({
      notifications: [],
      loading: false,
      error: null,
    })
    vi.clearAllMocks()
  })

  describe('addNotification', () => {
    it('should add notification to store on success', async () => {
      const mockAlert = {
        id: '1',
        personId: 'person-1',
        personName: 'Test Person',
        videoUrl: 'https://example.com/video.mp4',
        message: 'Test message',
        status: 'pending' as const,
        timestamp: '2024-01-01T00:00:00Z',
      }

      vi.mocked(alertService.create).mockResolvedValue(mockAlert)

      await useNotificationStore.getState().addNotification({
        personId: 'person-1',
        personName: 'Test Person',
        videoUrl: 'https://example.com/video.mp4',
        message: 'Test message',
      })

      const state = useNotificationStore.getState()
      expect(state.notifications).toHaveLength(1)
      expect(state.notifications[0].personName).toBe('Test Person')
      expect(state.loading).toBe(false)
    })
  })

  describe('updateNotificationStatus', () => {
    it('should update notification status to accepted', async () => {
      const notification = {
        id: '1',
        personId: 'person-1',
        personName: 'Test Person',
        videoUrl: 'https://example.com/video.mp4',
        message: 'Test message',
        status: 'pending' as const,
        timestamp: new Date('2024-01-01T00:00:00Z'),
      }

      useNotificationStore.setState({
        notifications: [notification],
      })

      // Mock service returns Alert format (timestamp as string)
      const updatedAlert = {
        id: '1',
        personId: 'person-1',
        personName: 'Test Person',
        videoUrl: 'https://example.com/video.mp4',
        message: 'Test message',
        status: 'accepted' as const,
        timestamp: '2024-01-01T00:00:00Z',
        decisionTimestamp: '2024-01-01T01:00:00Z',
      }

      vi.mocked(alertService.updateStatus).mockResolvedValue(updatedAlert)

      await useNotificationStore.getState().updateNotificationStatus('1', 'accepted')

      const state = useNotificationStore.getState()
      expect(state.notifications[0].status).toBe('accepted')
    })
  })

  describe('fetchNotifications', () => {
    it('should fetch and set notifications', async () => {
      const mockAlerts = [
        {
          id: '1',
          personId: 'person-1',
          personName: 'Person 1',
          videoUrl: 'https://example.com/video1.mp4',
          message: 'Message 1',
          status: 'pending' as const,
          timestamp: '2024-01-01T00:00:00Z',
        },
        {
          id: '2',
          personId: 'person-2',
          personName: 'Person 2',
          videoUrl: 'https://example.com/video2.mp4',
          message: 'Message 2',
          status: 'accepted' as const,
          timestamp: '2024-01-02T00:00:00Z',
        },
      ]

      vi.mocked(alertService.getAll).mockResolvedValue(mockAlerts as Alert[])

      await useNotificationStore.getState().fetchNotifications()

      const state = useNotificationStore.getState()
      expect(state.notifications).toHaveLength(2)
      expect(state.loading).toBe(false)
    })
  })

  describe('checkExpiredNotifications', () => {
    it('should mark expired pending notifications as unanswered', () => {
      const oldDate = new Date()
      oldDate.setMinutes(oldDate.getMinutes() - 10) // 10 minutes ago

      const notification = {
        id: '1',
        personId: 'person-1',
        personName: 'Test Person',
        videoUrl: 'https://example.com/video.mp4',
        message: 'Test message',
        status: 'pending' as const,
        timestamp: oldDate,
      }

      useNotificationStore.setState({
        notifications: [notification],
      })

      useNotificationStore.getState().checkExpiredNotifications()

      const state = useNotificationStore.getState()
      expect(state.notifications[0].status).toBe('unanswered')
    })

    it('should not change non-expired notifications', () => {
      const recentDate = new Date()
      recentDate.setMinutes(recentDate.getMinutes() - 2) // 2 minutes ago

      const notification = {
        id: '1',
        personId: 'person-1',
        personName: 'Test Person',
        videoUrl: 'https://example.com/video.mp4',
        message: 'Test message',
        status: 'pending' as const,
        timestamp: recentDate,
      }

      useNotificationStore.setState({
        notifications: [notification],
      })

      useNotificationStore.getState().checkExpiredNotifications()

      const state = useNotificationStore.getState()
      expect(state.notifications[0].status).toBe('pending')
    })
  })
})
