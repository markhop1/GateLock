import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import LoginPage from '../LoginPage'
import { useAuthStore } from '../../store/authStore'

// Mock auth store
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

describe('LoginPage', () => {
  const mockLogin = vi.fn()

  beforeEach(() => {
    vi.mocked(useAuthStore).mockImplementation((selector?: (state: any) => any) => {
      const state = {
        login: mockLogin,
        isAuthenticated: false,
        user: null,
        token: null,
        register: vi.fn(),
        logout: vi.fn(),
        checkAuth: vi.fn(),
      }
      return selector ? selector(state) : state
    })
    vi.clearAllMocks()
    mockNavigate.mockClear()
  })

  it('renders login form', () => {
    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/contraseña/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /iniciar sesión/i })).toBeInTheDocument()
  })

  it('shows error message on login failure', async () => {
    const user = userEvent.setup()
    const errorMessage = 'Invalid credentials'
    
    // Reset mock before each test
    mockLogin.mockReset()
    mockLogin.mockRejectedValue(new Error(errorMessage))

    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/contraseña/i)
    const submitButton = screen.getByRole('button', { name: /iniciar sesión/i })

    // Fill form
    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'wrong-password')

    // Submit form
    await user.click(submitButton)

    // Wait for error message to appear
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    }, { timeout: 3000 })
    
    // Verify login was called
    expect(mockLogin).toHaveBeenCalledWith('test@example.com', 'wrong-password')
  })

  it('navigates to home on successful login', async () => {
    const user = userEvent.setup()
    mockLogin.mockResolvedValue({
      token: 'test-token',
      user: { id: '1', email: 'test@example.com', name: 'Test User' },
    })

    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/contraseña/i)
    const submitButton = screen.getByRole('button', { name: /iniciar sesión/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/')
    })
  })
})
