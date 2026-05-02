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
})
