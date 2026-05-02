import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import SettingsPage from '../SettingsPage'
import { useAuthStore } from '../../store/authStore'

vi.mock('../../store/authStore', () => ({
  useAuthStore: vi.fn(),
}))

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

describe('SettingsPage', () => {
  const mockLogout = vi.fn()

  beforeEach(() => {
    vi.mocked(useAuthStore).mockImplementation((selector?: (state: any) => any) => {
      const state = {
        user: { id: '1', name: 'Test User', email: 'test@example.com' },
        logout: mockLogout,
      }
      return selector ? selector(state) : state
    })
    vi.clearAllMocks()
  })

  it('renders account information', () => {
    render(
      <BrowserRouter>
        <SettingsPage />
      </BrowserRouter>
    )

    expect(screen.getByText('Información de la cuenta')).toBeInTheDocument()
    expect(screen.getByText('Test User')).toBeInTheDocument()
    expect(screen.getByText('test@example.com')).toBeInTheDocument()
  })

  it('logs out and redirects to login', async () => {
    const user = userEvent.setup()

    render(
      <BrowserRouter>
        <SettingsPage />
      </BrowserRouter>
    )

    await user.click(screen.getByRole('button', { name: /cerrar sesión/i }))

    expect(mockLogout).toHaveBeenCalledTimes(1)
    expect(mockNavigate).toHaveBeenCalledWith('/login')
  })
})
