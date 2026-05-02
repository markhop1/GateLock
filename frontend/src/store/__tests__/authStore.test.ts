import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { useAuthStore } from '../authStore'
import { authService } from '../../services/auth.service'

// Mock auth service
vi.mock('../../services/auth.service', () => ({
  authService: {
    login: vi.fn(),
    register: vi.fn(),
    getMe: vi.fn(),
  },
}))

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(globalThis, 'localStorage', {
  value: localStorageMock,
})

describe('Auth Store', () => {
  beforeEach(() => {
    // Clear localStorage
    localStorageMock.getItem.mockReturnValue(null)
    localStorageMock.setItem.mockClear()
    localStorageMock.removeItem.mockClear()
    
    // Reset store state
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
    })
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('login', () => {
    it('should set user and token on successful login', async () => {
      const mockResponse = {
        token: 'test-token',
        user: {
          id: '1',
          email: 'test@example.com',
          name: 'Test User',
        },
      }

      vi.mocked(authService.login).mockResolvedValue(mockResponse)

      await useAuthStore.getState().login('test@example.com', 'password123')

      const state = useAuthStore.getState()
      expect(state.user).toEqual(mockResponse.user)
      expect(state.token).toBe(mockResponse.token)
      expect(state.isAuthenticated).toBe(true)
    })

    it('should throw error on failed login', async () => {
      const error = new Error('Invalid credentials')
      vi.mocked(authService.login).mockRejectedValue(error)

      await expect(
        useAuthStore.getState().login('test@example.com', 'wrong-password')
      ).rejects.toThrow()
    })
  })

  describe('logout', () => {
    it('should clear user and token', () => {
      useAuthStore.setState({
        user: { id: '1', email: 'test@example.com', name: 'Test User' },
        token: 'test-token',
        isAuthenticated: true,
      })

      useAuthStore.getState().logout()

      const state = useAuthStore.getState()
      expect(state.user).toBeNull()
      expect(state.token).toBeNull()
      expect(state.isAuthenticated).toBe(false)
    })
  })

  describe('register', () => {
    it('should set user and token on successful register', async () => {
      const mockResponse = {
        token: 'register-token',
        user: {
          id: '2',
          email: 'new@example.com',
          name: 'New User',
        },
      }

      vi.mocked(authService.register).mockResolvedValue(mockResponse)

      await useAuthStore.getState().register('new@example.com', 'password123', 'New User')

      const state = useAuthStore.getState()
      expect(state.user).toEqual(mockResponse.user)
      expect(state.token).toBe(mockResponse.token)
      expect(state.isAuthenticated).toBe(true)
    })
  })

  describe('checkAuth', () => {
    it('should keep user authenticated when getMe succeeds', async () => {
      const user = {
        id: '1',
        email: 'test@example.com',
        name: 'Test User',
      }

      vi.mocked(authService.getMe).mockResolvedValue({ user })

      await useAuthStore.getState().checkAuth()

      const state = useAuthStore.getState()
      expect(state.user).toEqual(user)
      expect(state.isAuthenticated).toBe(true)
    })

    it('should reset auth state when getMe fails', async () => {
      useAuthStore.setState({
        user: { id: '1', email: 'test@example.com', name: 'Test User' },
        token: 'token',
        isAuthenticated: true,
      })

      vi.mocked(authService.getMe).mockRejectedValue(new Error('Unauthorized'))

      await useAuthStore.getState().checkAuth()

      const state = useAuthStore.getState()
      expect(state.user).toBeNull()
      expect(state.token).toBeNull()
      expect(state.isAuthenticated).toBe(false)
    })
  })
})
