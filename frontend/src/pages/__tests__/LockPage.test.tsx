import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LockPage from '../LockPage'
import { nukiService } from '../../services/nuki.service'

vi.mock('../../services/nuki.service', () => ({
  nukiService: {
    getStatus: vi.fn(),
    unlock: vi.fn(),
    lock: vi.fn(),
  },
}))

describe('LockPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows not configured notice', async () => {
    vi.mocked(nukiService.getStatus).mockResolvedValue({ configured: false, notConfigured: true })

    render(<LockPage />)

    expect(await screen.findByText(/candado no configurado/i)).toBeInTheDocument()
  })

  it('shows unavailable error when status fetch fails', async () => {
    vi.mocked(nukiService.getStatus).mockRejectedValue(new Error('network'))
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => undefined)

    render(<LockPage />)

    const errorMessages = await screen.findAllByText(/no se ha podido obtener el estado del candado/i)
    expect(errorMessages.length).toBeGreaterThan(0)
    consoleSpy.mockRestore()
  })

  it('unlocks successfully from locked state', async () => {
    const user = userEvent.setup()
    vi.mocked(nukiService.getStatus)
      .mockResolvedValueOnce({ configured: true, status: 'locked', name: 'Puerta' })
      .mockResolvedValueOnce({ configured: true, status: 'unlocked', name: 'Puerta' })
    vi.mocked(nukiService.unlock).mockResolvedValue(undefined)

    render(<LockPage />)

    const unlockButton = await screen.findByRole('button', { name: /abrir/i })
    await user.click(unlockButton)

    await waitFor(() => {
      expect(nukiService.unlock).toHaveBeenCalledTimes(1)
    })

    expect(await screen.findByText(/comando ejecutado correctamente/i)).toBeInTheDocument()
  })

  it('locks successfully from unlocked state', async () => {
    const user = userEvent.setup()
    vi.mocked(nukiService.getStatus)
      .mockResolvedValueOnce({ configured: true, status: 'unlocked', name: 'Puerta' })
      .mockResolvedValueOnce({ configured: true, status: 'locked', name: 'Puerta' })
    vi.mocked(nukiService.lock).mockResolvedValue(undefined)

    render(<LockPage />)

    const lockButton = await screen.findByRole('button', { name: /cerrar/i })
    await user.click(lockButton)

    await waitFor(() => {
      expect(nukiService.lock).toHaveBeenCalledTimes(1)
    })

    expect(await screen.findByText(/comando ejecutado correctamente/i)).toBeInTheDocument()
  })

  it('shows retry block when status is unknown', async () => {
    vi.mocked(nukiService.getStatus).mockResolvedValue({
      configured: true,
      status: 'unknown',
      error: true,
    })

    render(<LockPage />)

    expect(await screen.findByText(/comprueba la conexión con nuki web/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /reintentar/i })).toBeInTheDocument()
  })
})
