import { describe, it, expect, beforeEach, vi } from 'vitest'
import { Request, Response } from 'express'
import { register, login } from '../auth.controller.js'

describe('Auth Controller - Validation', () => {
  let mockReq: Partial<Request>
  let mockRes: Partial<Response>
  let mockNext: ReturnType<typeof vi.fn>

  beforeEach(() => {
    mockReq = {
      body: {},
    }
    mockRes = {
      status: vi.fn().mockReturnThis(),
      json: vi.fn().mockReturnThis(),
    }
    mockNext = vi.fn()
    vi.clearAllMocks()
  })

  describe('register - input validation', () => {
    it('should return 400 if email is missing', async () => {
      mockReq.body = { password: 'password123', name: 'Test User' }

      await register(mockReq as Request, mockRes as Response, mockNext)

      expect(mockRes.status).toHaveBeenCalledWith(400)
      expect(mockRes.json).toHaveBeenCalledWith({
        error: 'Email, password, and name are required',
      })
    })

    it('should return 400 if password is missing', async () => {
      mockReq.body = { email: 'test@example.com', name: 'Test User' }

      await register(mockReq as Request, mockRes as Response, mockNext)

      expect(mockRes.status).toHaveBeenCalledWith(400)
      expect(mockRes.json).toHaveBeenCalledWith({
        error: 'Email, password, and name are required',
      })
    })

    it('should return 400 if name is missing', async () => {
      mockReq.body = { email: 'test@example.com', password: 'password123' }

      await register(mockReq as Request, mockRes as Response, mockNext)

      expect(mockRes.status).toHaveBeenCalledWith(400)
      expect(mockRes.json).toHaveBeenCalledWith({
        error: 'Email, password, and name are required',
      })
    })

    it('should return 400 if email format is invalid', async () => {
      mockReq.body = {
        email: 'invalid-email',
        password: 'password123',
        name: 'Test User',
      }

      await register(mockReq as Request, mockRes as Response, mockNext)

      expect(mockRes.status).toHaveBeenCalledWith(400)
      expect(mockRes.json).toHaveBeenCalledWith({
        error: 'Please provide a valid email address',
      })
    })

    it('should return 400 if password is too short', async () => {
      mockReq.body = {
        email: 'test@example.com',
        password: '12345',
        name: 'Test User',
      }

      await register(mockReq as Request, mockRes as Response, mockNext)

      expect(mockRes.status).toHaveBeenCalledWith(400)
      expect(mockRes.json).toHaveBeenCalledWith({
        error: 'Password must be at least 6 characters long',
      })
    })

    it('should return 400 if name is too short', async () => {
      mockReq.body = {
        email: 'test@example.com',
        password: 'password123',
        name: 'A',
      }

      await register(mockReq as Request, mockRes as Response, mockNext)

      expect(mockRes.status).toHaveBeenCalledWith(400)
      expect(mockRes.json).toHaveBeenCalledWith({
        error: 'Name must be at least 2 characters long',
      })
    })
  })

  describe('login - input validation', () => {
    it('should return 400 if email is missing', async () => {
      mockReq.body = { password: 'password123' }

      await login(mockReq as Request, mockRes as Response, mockNext)

      expect(mockRes.status).toHaveBeenCalledWith(400)
      expect(mockRes.json).toHaveBeenCalledWith({
        error: 'Email and password are required',
      })
    })

    it('should return 400 if password is missing', async () => {
      mockReq.body = { email: 'test@example.com' }

      await login(mockReq as Request, mockRes as Response, mockNext)

      expect(mockRes.status).toHaveBeenCalledWith(400)
      expect(mockRes.json).toHaveBeenCalledWith({
        error: 'Email and password are required',
      })
    })
  })
})
