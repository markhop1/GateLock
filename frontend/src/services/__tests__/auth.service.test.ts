import { describe, it, expect, beforeEach, vi } from 'vitest'
import { authService } from '../auth.service'
import api from '../api'

vi.mock('../api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

describe('authService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('login', () => {
    it('should return token and user on successful login', async () => {
      const credentials = { email: 'test@example.com', password: 'password123' }
      const mockResponse = {
        token: 'jwt-token-123',
        user: { id: '1', email: 'test@example.com', name: 'Test User' },
      }
      vi.mocked(api.post).mockResolvedValue({ data: mockResponse })

      const result = await authService.login(credentials)

      expect(api.post).toHaveBeenCalledWith('/auth/login', credentials)
      expect(result).toEqual(mockResponse)
    })

    it('should propagate errors on failed login', async () => {
      vi.mocked(api.post).mockRejectedValue(new Error('Invalid credentials'))

      await expect(authService.login({ email: 'bad@test.com', password: 'wrong' })).rejects.toThrow(
        'Invalid credentials'
      )
    })
  })

  describe('register', () => {
    it('should return token and user on successful registration', async () => {
      const data = { email: 'new@example.com', password: 'secret', name: 'New User' }
      const mockResponse = {
        token: 'jwt-token-456',
        user: { id: '2', email: 'new@example.com', name: 'New User' },
      }
      vi.mocked(api.post).mockResolvedValue({ data: mockResponse })

      const result = await authService.register(data)

      expect(api.post).toHaveBeenCalledWith('/auth/register', data)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getMe', () => {
    it('should return current user', async () => {
      const mockUser = { id: '1', email: 'test@example.com', name: 'Test User' }
      vi.mocked(api.get).mockResolvedValue({ data: { user: mockUser } })

      const result = await authService.getMe()

      expect(api.get).toHaveBeenCalledWith('/auth/me')
      expect(result).toEqual({ user: mockUser })
    })
  })
})
