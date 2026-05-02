import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import NotificationCard from '../NotificationCard'
import { Notification } from '../../store/notificationStore'

describe('NotificationCard', () => {
  const mockNotification: Notification = {
    id: '1',
    personId: 'person-1',
    personName: 'Juan Pérez',
    videoUrl: 'https://example.com/video.mp4',
    message: 'Juan Pérez quiere acceder, ¿permitir?',
    status: 'pending',
    timestamp: new Date('2024-01-01T12:00:00'),
  }

  it('renders notification information', () => {
    const onAction = vi.fn()
    render(<NotificationCard notification={mockNotification} onAction={onAction} />)

    // Check for the heading (h3)
    expect(screen.getByRole('heading', { name: /Juan Pérez quiere acceder/i })).toBeInTheDocument()
    // Check for the message paragraph
    expect(screen.getByText(/Juan Pérez quiere acceder, ¿permitir\?/i)).toBeInTheDocument()
  })

  it('shows action buttons for pending notifications', () => {
    const onAction = vi.fn()
    render(<NotificationCard notification={mockNotification} onAction={onAction} />)

    expect(screen.getByRole('button', { name: /abrir/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /ignorar/i })).toBeInTheDocument()
  })

  it('does not show action buttons for non-pending notifications', () => {
    const acceptedNotification = { ...mockNotification, status: 'accepted' as const }
    const onAction = vi.fn()
    render(<NotificationCard notification={acceptedNotification} onAction={onAction} />)

    expect(screen.queryByRole('button', { name: /abrir/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /ignorar/i })).not.toBeInTheDocument()
  })

  it('shows status icon and text for non-pending notifications', () => {
    const acceptedNotification = { ...mockNotification, status: 'accepted' as const }
    const onAction = vi.fn()
    render(<NotificationCard notification={acceptedNotification} onAction={onAction} />)

    expect(screen.getByText(/aceptada/i)).toBeInTheDocument()
  })

  it('shows ignored status text', () => {
    const ignoredNotification = { ...mockNotification, status: 'ignored' as const }
    const onAction = vi.fn()
    render(<NotificationCard notification={ignoredNotification} onAction={onAction} />)

    expect(screen.getByText(/ignorada/i)).toBeInTheDocument()
  })

  it('shows unanswered status text', () => {
    const unansweredNotification = { ...mockNotification, status: 'unanswered' as const }
    const onAction = vi.fn()
    render(<NotificationCard notification={unansweredNotification} onAction={onAction} />)

    expect(screen.getByText(/no respondida/i)).toBeInTheDocument()
  })

  it('does not show action buttons when showActions is false', () => {
    const onAction = vi.fn()
    render(
      <NotificationCard
        notification={mockNotification}
        onAction={onAction}
        showActions={false}
      />
    )

    expect(screen.queryByRole('button', { name: /abrir/i })).not.toBeInTheDocument()
  })

  it('calls onAction when button is clicked', async () => {
    const user = userEvent.setup()
    const onAction = vi.fn()
    render(<NotificationCard notification={mockNotification} onAction={onAction} />)

    const abrirButton = screen.getByRole('button', { name: /abrir/i })
    await user.click(abrirButton)
    
    expect(onAction).toHaveBeenCalledWith('1', 'accepted')
  })
})
