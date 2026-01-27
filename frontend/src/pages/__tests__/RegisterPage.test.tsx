import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import RegisterPage from '../RegisterPage'
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

describe('RegisterPage', () => {
  const mockRegister = vi.fn()

  beforeEach(() => {
    vi.mocked(useAuthStore).mockImplementation((selector?: (state: any) => any) => {
      const state = {
        register: mockRegister,
        isAuthenticated: false,
        user: null,
        token: null,
        login: vi.fn(),
        logout: vi.fn(),
        checkAuth: vi.fn(),
      }
      return selector ? selector(state) : state
    })
    vi.clearAllMocks()
    mockNavigate.mockClear()
  })

  it('renders registration form', () => {
    render(
      <BrowserRouter>
        <RegisterPage />
      </BrowserRouter>
    )

    expect(screen.getByLabelText('Nombre')).toBeInTheDocument()
    expect(screen.getByLabelText('Email')).toBeInTheDocument()
    expect(screen.getByLabelText('Contraseña')).toBeInTheDocument()
    expect(screen.getByLabelText('Confirmar contraseña')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /registrarse/i })).toBeInTheDocument()
  })

  it('shows error if passwords do not match', async () => {
    const user = userEvent.setup()

    render(
      <BrowserRouter>
        <RegisterPage />
      </BrowserRouter>
    )

    const nameInput = screen.getByLabelText('Nombre')
    const emailInput = screen.getByLabelText('Email')
    const passwordInput = screen.getByLabelText('Contraseña')
    const confirmPasswordInput = screen.getByLabelText('Confirmar contraseña')
    const submitButton = screen.getByRole('button', { name: /registrarse/i })

    await user.type(nameInput, 'Test User')
    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(confirmPasswordInput, 'different-password')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/las contraseñas no coinciden/i)).toBeInTheDocument()
    })

    expect(mockRegister).not.toHaveBeenCalled()
  })

  it('shows error if password is too short', async () => {
    const user = userEvent.setup()

    render(
      <BrowserRouter>
        <RegisterPage />
      </BrowserRouter>
    )

    const nameInput = screen.getByLabelText('Nombre')
    const emailInput = screen.getByLabelText('Email')
    const passwordInput = screen.getByLabelText('Contraseña')
    const confirmPasswordInput = screen.getByLabelText('Confirmar contraseña')
    const submitButton = screen.getByRole('button', { name: /registrarse/i })

    await user.type(nameInput, 'Test User')
    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, '12345')
    await user.type(confirmPasswordInput, '12345')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/la contraseña debe tener al menos 6 caracteres/i)).toBeInTheDocument()
    })

    expect(mockRegister).not.toHaveBeenCalled()
  })

  it('navigates to home on successful registration', async () => {
    const user = userEvent.setup()
    mockRegister.mockResolvedValue({
      token: 'test-token',
      user: { id: '1', email: 'test@example.com', name: 'Test User' },
    })

    render(
      <BrowserRouter>
        <RegisterPage />
      </BrowserRouter>
    )

    const nameInput = screen.getByLabelText('Nombre')
    const emailInput = screen.getByLabelText('Email')
    const passwordInput = screen.getByLabelText('Contraseña')
    const confirmPasswordInput = screen.getByLabelText('Confirmar contraseña')
    const submitButton = screen.getByRole('button', { name: /registrarse/i })

    await user.type(nameInput, 'Test User')
    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(confirmPasswordInput, 'password123')
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/')
    })
  })
})
