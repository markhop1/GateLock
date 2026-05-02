import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { useQuickLogin } from '../useQuickLogin'
import { useAuthStore } from '../../store/authStore'

vi.mock('../../store/authStore', () => ({
  useAuthStore: {
    getState: vi.fn(),
  },
}))

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

function HookHarness() {
  useQuickLogin()
  return null
}

describe('useQuickLogin', () => {
  const login = vi.fn()
  const register = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    vi.spyOn(window, 'alert').mockImplementation(() => undefined)
  })

  it('logs in with shortcut when test user exists', async () => {
    login.mockResolvedValue(undefined)
    vi.mocked(useAuthStore.getState).mockReturnValue({
      login,
      register,
      isAuthenticated: false,
    })

    render(
      <BrowserRouter>
        <HookHarness />
      </BrowserRouter>
    )

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'K', ctrlKey: true, shiftKey: true }))

    await waitFor(() => {
      expect(login).toHaveBeenCalledWith('test@example.com', 'test123')
      expect(mockNavigate).toHaveBeenCalledWith('/')
    })
  })

  it('registers and then logs in when first login fails', async () => {
    login.mockRejectedValueOnce(new Error('not found')).mockResolvedValueOnce(undefined)
    register.mockResolvedValue(undefined)
    vi.mocked(useAuthStore.getState).mockReturnValue({
      login,
      register,
      isAuthenticated: false,
    })

    render(
      <BrowserRouter>
        <HookHarness />
      </BrowserRouter>
    )

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'K', ctrlKey: true, shiftKey: true }))

    await waitFor(() => {
      expect(register).toHaveBeenCalledWith('test@example.com', 'test123', 'Test User')
      expect(login).toHaveBeenCalledTimes(2)
      expect(mockNavigate).toHaveBeenCalledWith('/')
    })
  })
})
