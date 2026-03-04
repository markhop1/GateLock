import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import HomePage from '../HomePage'
import { useNotificationStore } from '../../store/notificationStore'

vi.mock('../../store/notificationStore', () => ({
  useNotificationStore: vi.fn(),
}))

describe('HomePage', () => {
  const mockFetchNotifications = vi.fn()
  const mockUpdateNotificationStatus = vi.fn()
  const mockCheckExpiredNotifications = vi.fn()
  const mockAddNotification = vi.fn()

  beforeEach(() => {
    vi.mocked(useNotificationStore).mockImplementation((selector) => {
      const state = {
        notifications: [],
        fetchNotifications: mockFetchNotifications,
        updateNotificationStatus: mockUpdateNotificationStatus,
        checkExpiredNotifications: mockCheckExpiredNotifications,
        addNotification: mockAddNotification,
      }
      return selector ? selector(state) : state
    })
    vi.clearAllMocks()
  })

  it('renders title and tip section', () => {
    render(<HomePage />)

    expect(screen.getByRole('heading', { name: /notificaciones/i })).toBeInTheDocument()
    expect(screen.getByText(/gestiona las solicitudes de acceso/i)).toBeInTheDocument()
    expect(screen.getByText(/simulateNotification/)).toBeInTheDocument()
  })

  it('calls fetchNotifications on mount', () => {
    render(<HomePage />)

    expect(mockFetchNotifications).toHaveBeenCalled()
  })

  it('shows empty state when no pending notifications', () => {
    render(<HomePage />)

    expect(screen.getByText(/no hay notificaciones pendientes/i)).toBeInTheDocument()
    expect(screen.getByText(/las nuevas solicitudes de acceso aparecerán aquí/i)).toBeInTheDocument()
  })

  it('renders NotificationCards when there are pending notifications', () => {
    const mockNotification = {
      id: 'n1',
      personId: 'p1',
      personName: 'Juan Pérez',
      videoUrl: '/videos/1.mp4',
      message: 'Quiere acceder',
      status: 'pending' as const,
      timestamp: new Date('2025-01-01T12:00:00'),
    }
    vi.mocked(useNotificationStore).mockImplementation((selector) => {
      const state = {
        notifications: [mockNotification],
        fetchNotifications: mockFetchNotifications,
        updateNotificationStatus: mockUpdateNotificationStatus,
        checkExpiredNotifications: mockCheckExpiredNotifications,
        addNotification: mockAddNotification,
      }
      return selector ? selector(state) : state
    })

    render(<HomePage />)

    expect(screen.getByText('Juan Pérez')).toBeInTheDocument()
    expect(screen.getByText(/quiere acceder/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /abrir/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /ignorar/i })).toBeInTheDocument()
  })
})
