import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import HomePage from '../HomePage'
import { useNotificationStore } from '../../store/notificationStore'
import { nukiService } from '../../services/nuki.service'

vi.mock('../../store/notificationStore', () => ({
  useNotificationStore: vi.fn(),
}))

vi.mock('../../services/nuki.service', () => ({
  nukiService: { getStatus: vi.fn() },
}))

describe('HomePage', () => {
  const mockFetchNotifications = vi.fn()
  const mockUpdateNotificationStatus = vi.fn()
  const mockCheckExpiredNotifications = vi.fn()
  const mockAddNotification = vi.fn()
  let mockNotifications: Array<{
    id: string
    personId: string
    personName: string
    videoUrl: string
    message: string
    status: 'pending'
    timestamp: Date
  }>

  beforeEach(() => {
    mockNotifications = []
    vi.mocked(useNotificationStore).mockImplementation((selector) => {
      const state = {
        notifications: mockNotifications,
        fetchNotifications: mockFetchNotifications,
        updateNotificationStatus: mockUpdateNotificationStatus,
        checkExpiredNotifications: mockCheckExpiredNotifications,
        addNotification: mockAddNotification,
      }
      return selector ? selector(state) : state
    })
    vi.clearAllMocks()
    vi.mocked(nukiService.getStatus).mockResolvedValue({
      configured: true,
      status: 'locked',
    })
  })

  const renderHome = async () => {
    render(<HomePage />)
    await waitFor(() => {
      expect(nukiService.getStatus).toHaveBeenCalled()
    })
  }

  it('renders title and description', async () => {
    await renderHome()

    expect(screen.getByRole('heading', { level: 1, name: /notificaciones/i })).toBeInTheDocument()
    expect(screen.getByText(/gestiona las solicitudes de acceso/i)).toBeInTheDocument()
    // Tip is only shown in dev mode (import.meta.env.DEV)
  })

  it('calls fetchNotifications on mount', async () => {
    await renderHome()

    expect(mockFetchNotifications).toHaveBeenCalled()
  })

  it('shows empty state when no pending notifications', async () => {
    await renderHome()

    expect(screen.getByText(/no hay notificaciones pendientes/i)).toBeInTheDocument()
    expect(screen.getByText(/las nuevas solicitudes de acceso aparecerán aquí/i)).toBeInTheDocument()
  })

  it('renders NotificationCards when there are pending notifications', async () => {
    const mockNotification = {
      id: 'n1',
      personId: 'p1',
      personName: 'Juan Pérez',
      videoUrl: '/videos/1.mp4',
      message: 'Quiere acceder',
      status: 'pending' as const,
      timestamp: new Date('2025-01-01T12:00:00'),
    }
    mockNotifications = [mockNotification]
    vi.mocked(useNotificationStore).mockImplementation((selector) => {
      const state = {
        notifications: mockNotifications,
        fetchNotifications: mockFetchNotifications,
        updateNotificationStatus: mockUpdateNotificationStatus,
        checkExpiredNotifications: mockCheckExpiredNotifications,
        addNotification: mockAddNotification,
      }
      return selector ? selector(state) : state
    })

    await renderHome()

    expect(await screen.findByRole('heading', { name: /juan pérez/i })).toBeInTheDocument()
    expect(screen.getAllByText(/quiere acceder/i).length).toBeGreaterThan(0)
    expect(screen.getByRole('button', { name: /abrir/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /ignorar/i })).toBeInTheDocument()
  })

  it('shows notice when lock is not configured', async () => {
    vi.mocked(nukiService.getStatus).mockResolvedValue({
      configured: false,
      notConfigured: true,
    })

    await renderHome()

    expect(screen.getByText(/candado no configurado/i)).toBeInTheDocument()
  })

  it('shows connection notice when lock status is unavailable', async () => {
    vi.mocked(nukiService.getStatus).mockResolvedValue({
      configured: true,
      status: 'unavailable',
      error: true,
    })

    await renderHome()

    expect(screen.getByText(/no se ha podido obtener el estado del candado/i)).toBeInTheDocument()
  })

  it('handles accepted notification action and refreshes data', async () => {
    const mockNotification = {
      id: 'n1',
      personId: 'p1',
      personName: 'Juan Pérez',
      videoUrl: '/videos/1.mp4',
      message: 'Quiere acceder',
      status: 'pending' as const,
      timestamp: new Date('2025-01-01T12:00:00'),
    }
    mockNotifications = [mockNotification]
    vi.mocked(useNotificationStore).mockImplementation((selector) => {
      const state = {
        notifications: mockNotifications,
        fetchNotifications: mockFetchNotifications,
        updateNotificationStatus: mockUpdateNotificationStatus,
        checkExpiredNotifications: mockCheckExpiredNotifications,
        addNotification: mockAddNotification,
      }
      return selector ? selector(state) : state
    })

    await renderHome()

    const abrirButton = await screen.findByRole('button', { name: /abrir/i })
    abrirButton.click()

    await waitFor(() => {
      expect(mockUpdateNotificationStatus).toHaveBeenCalledWith('n1', 'accepted')
      expect(mockFetchNotifications).toHaveBeenCalled()
    })
  })

  it('handles ignored notification action', async () => {
    const mockNotification = {
      id: 'n1',
      personId: 'p1',
      personName: 'Juan Pérez',
      videoUrl: '/videos/1.mp4',
      message: 'Quiere acceder',
      status: 'pending' as const,
      timestamp: new Date('2025-01-01T12:00:00'),
    }
    mockNotifications = [mockNotification]
    vi.mocked(useNotificationStore).mockImplementation((selector) => {
      const state = {
        notifications: mockNotifications,
        fetchNotifications: mockFetchNotifications,
        updateNotificationStatus: mockUpdateNotificationStatus,
        checkExpiredNotifications: mockCheckExpiredNotifications,
        addNotification: mockAddNotification,
      }
      return selector ? selector(state) : state
    })

    await renderHome()

    const ignoreButton = await screen.findByRole('button', { name: /ignorar/i })
    ignoreButton.click()

    await waitFor(() => {
      expect(mockUpdateNotificationStatus).toHaveBeenCalledWith('n1', 'ignored')
    })
  })
})
