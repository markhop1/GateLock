import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import HistoryPage from '../HistoryPage'
import { useNotificationStore } from '../../store/notificationStore'

vi.mock('../../store/notificationStore', () => ({
  useNotificationStore: vi.fn(),
}))

describe('HistoryPage', () => {
  const mockFetchNotifications = vi.fn()

  beforeEach(() => {
    vi.mocked(useNotificationStore).mockImplementation((selector) => {
      const state = {
        notifications: [],
        fetchNotifications: mockFetchNotifications,
      }
      return selector ? selector(state) : state
    })
    vi.clearAllMocks()
  })

  it('renders title and description', () => {
    render(
      <BrowserRouter>
        <HistoryPage />
      </BrowserRouter>
    )

    expect(screen.getByRole('heading', { name: /historial de alertas/i })).toBeInTheDocument()
    expect(screen.getByText(/todas las solicitudes de acceso registradas/i)).toBeInTheDocument()
  })

  it('calls fetchNotifications on mount', () => {
    render(
      <BrowserRouter>
        <HistoryPage />
      </BrowserRouter>
    )

    expect(mockFetchNotifications).toHaveBeenCalled()
  })

  it('shows empty state when no notifications', () => {
    render(
      <BrowserRouter>
        <HistoryPage />
      </BrowserRouter>
    )

    expect(screen.getByText(/no hay alertas registradas/i)).toBeInTheDocument()
    expect(screen.getByText(/el historial aparecerá aquí cuando haya solicitudes/i)).toBeInTheDocument()
  })

  it('renders notification list when there are notifications', () => {
    const mockNotifications = [
      {
        id: '1',
        personId: 'p1',
        personName: 'María García',
        videoUrl: '/videos/1.mp4',
        message: 'Test',
        status: 'accepted' as const,
        timestamp: new Date('2025-01-01T10:00:00'),
      },
      {
        id: '2',
        personId: 'p2',
        personName: 'Carlos López',
        videoUrl: '/videos/2.mp4',
        message: 'Test 2',
        status: 'ignored' as const,
        timestamp: new Date('2025-01-01T11:00:00'),
      },
    ]
    vi.mocked(useNotificationStore).mockImplementation((selector) => {
      const state = {
        notifications: mockNotifications,
        fetchNotifications: mockFetchNotifications,
      }
      return selector ? selector(state) : state
    })

    render(
      <BrowserRouter>
        <HistoryPage />
      </BrowserRouter>
    )

    expect(screen.getByText('María García')).toBeInTheDocument()
    expect(screen.getByText('Carlos López')).toBeInTheDocument()
    expect(screen.getByText(/aceptada/i)).toBeInTheDocument()
    expect(screen.getByText(/ignorada/i)).toBeInTheDocument()
  })
})
