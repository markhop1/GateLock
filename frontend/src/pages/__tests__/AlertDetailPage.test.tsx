import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import AlertDetailPage from '../AlertDetailPage'
import { useNotificationStore } from '../../store/notificationStore'

vi.mock('../../store/notificationStore', () => ({
  useNotificationStore: vi.fn(),
}))

vi.mock('../../services/alert.service', () => ({
  alertService: {
    getById: vi.fn().mockResolvedValue({}),
  },
}))

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/history/:id" element={<AlertDetailPage />} />
      </Routes>
    </MemoryRouter>
  )
}

describe('AlertDetailPage', () => {
  const mockGetNotificationById = vi.fn()
  const mockFetchNotifications = vi.fn()

  beforeEach(() => {
    vi.mocked(useNotificationStore).mockImplementation((selector) => {
      const state = {
        getNotificationById: mockGetNotificationById,
        fetchNotifications: mockFetchNotifications,
      }
      return selector ? selector(state) : state
    })
    vi.clearAllMocks()
  })

  it('shows not found when notification does not exist', () => {
    mockGetNotificationById.mockReturnValue(undefined)

    renderAt('/history/999')

    expect(screen.getByText(/alerta no encontrada/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /volver al historial/i })).toHaveAttribute('href', '/history')
  })

  it('renders alert detail when notification exists', () => {
    const mockNotification = {
      id: '1',
      personId: 'p1',
      personName: 'Juan Pérez',
      videoUrl: '/uploads/videos/test.mp4',
      message: 'Quiere acceder a la propiedad',
      status: 'accepted' as const,
      timestamp: new Date('2025-01-15T10:30:00'),
      decisionTimestamp: new Date('2025-01-15T10:35:00'),
    }
    mockGetNotificationById.mockReturnValue(mockNotification)

    renderAt('/history/1')

    expect(screen.getByRole('heading', { name: /detalle de la alerta/i })).toBeInTheDocument()
    expect(screen.getByText('Juan Pérez')).toBeInTheDocument()
    expect(screen.getByText(/quiere acceder a la propiedad/i)).toBeInTheDocument()
    expect(screen.getByText(/aceptada/i)).toBeInTheDocument()
    expect(screen.getByText(/persona detectada/i)).toBeInTheDocument()
    expect(screen.getByText(/mensaje/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /volver al historial/i })).toBeInTheDocument()
  })

  it('shows video section when videoUrl exists', () => {
    const mockNotification = {
      id: '1',
      personId: 'p1',
      personName: 'María',
      videoUrl: '/uploads/videos/vid.mp4',
      message: 'Test',
      status: 'pending' as const,
      timestamp: new Date('2025-01-01T12:00:00'),
    }
    mockGetNotificationById.mockReturnValue(mockNotification)

    renderAt('/history/1')

    const video = screen.getByTitle(/clip de maría/i)
    expect(video).toBeInTheDocument()
    expect(video).toHaveAttribute('src')
  })

  it('shows different status labels', () => {
    const mockNotification = {
      id: '1',
      personId: 'p1',
      personName: 'Test',
      videoUrl: '',
      message: 'Msg',
      status: 'ignored' as const,
      timestamp: new Date('2025-01-01'),
    }
    mockGetNotificationById.mockReturnValue(mockNotification)

    renderAt('/history/1')

    expect(screen.getByText(/ignorada/i)).toBeInTheDocument()
  })
})
