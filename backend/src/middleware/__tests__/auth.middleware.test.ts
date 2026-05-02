import { describe, it, expect, beforeEach, vi } from 'vitest'
import { Response } from 'express'
import { authenticate, AuthRequest } from '../auth.middleware.js'
import jwt from 'jsonwebtoken'
import { User } from '../../models/User.model.js'

// Mock dependencies
vi.mock('jsonwebtoken')
vi.mock('../../models/User.model.js', () => ({
  User: {
    findById: vi.fn(),
  },
}))

describe('Auth Middleware', () => {
  let mockReq: Partial<AuthRequest>
  let mockRes: Partial<Response>
  let mockNext: ReturnType<typeof vi.fn>

  beforeEach(() => {
    mockReq = {
      headers: {},
    }
    mockRes = {
      status: vi.fn().mockReturnThis(),
      json: vi.fn().mockReturnThis(),
    }
    mockNext = vi.fn()
    vi.clearAllMocks()
    process.env.JWT_SECRET = 'test-secret'
  })

  it('should return 401 if no token is provided', async () => {
    await authenticate(mockReq as AuthRequest, mockRes as Response, mockNext)

    expect(mockRes.status).toHaveBeenCalledWith(401)
    expect(mockRes.json).toHaveBeenCalledWith({
      error: 'Authentication required',
    })
    expect(mockNext).not.toHaveBeenCalled()
  })

  it('should return 500 if JWT_SECRET is not configured', async () => {
    delete process.env.JWT_SECRET
    mockReq.headers = {
      authorization: 'Bearer valid-token',
    }

    await authenticate(mockReq as AuthRequest, mockRes as Response, mockNext)

    expect(mockRes.status).toHaveBeenCalledWith(500)
    expect(mockRes.json).toHaveBeenCalledWith({
      error: 'Server configuration error',
    })
  })

  it('should return 401 if token is invalid', async () => {
    process.env.JWT_SECRET = 'test-secret'
    mockReq.headers = {
      authorization: 'Bearer invalid-token',
    }

    vi.mocked(jwt.verify).mockImplementation(() => {
      throw new jwt.JsonWebTokenError('Invalid token')
    })

    await authenticate(mockReq as AuthRequest, mockRes as Response, mockNext)

    expect(mockRes.status).toHaveBeenCalledWith(401)
    expect(mockRes.json).toHaveBeenCalledWith({
      error: 'Invalid token',
    })
  })

  it('should return 401 if user from token does not exist', async () => {
    process.env.JWT_SECRET = 'test-secret'
    mockReq.headers = {
      authorization: 'Bearer valid-token',
    }

    vi.mocked(jwt.verify).mockReturnValue({ userId: 'user-id-1' } as never)
    vi.mocked(User.findById).mockReturnValue({
      select: vi.fn().mockResolvedValue(null),
    } as never)

    await authenticate(mockReq as AuthRequest, mockRes as Response, mockNext)

    expect(mockRes.status).toHaveBeenCalledWith(401)
    expect(mockRes.json).toHaveBeenCalledWith({ error: 'User not found' })
    expect(mockNext).not.toHaveBeenCalled()
  })

  it('should attach user and call next when token is valid', async () => {
    process.env.JWT_SECRET = 'test-secret'
    mockReq.headers = {
      authorization: 'Bearer valid-token',
    }

    const mockUser = {
      _id: { toString: () => 'user-id-1' },
      email: 'test@example.com',
      name: 'Test User',
    }

    vi.mocked(jwt.verify).mockReturnValue({ userId: 'user-id-1' } as never)
    vi.mocked(User.findById).mockReturnValue({
      select: vi.fn().mockResolvedValue(mockUser),
    } as never)

    await authenticate(mockReq as AuthRequest, mockRes as Response, mockNext)

    expect(mockReq.userId).toBe('user-id-1')
    expect(mockReq.user).toEqual({
      id: 'user-id-1',
      email: 'test@example.com',
      name: 'Test User',
    })
    expect(mockNext).toHaveBeenCalledTimes(1)
  })

  it('should forward non-jwt errors to next', async () => {
    process.env.JWT_SECRET = 'test-secret'
    mockReq.headers = {
      authorization: 'Bearer valid-token',
    }

    const unknownError = new Error('unexpected')
    vi.mocked(jwt.verify).mockImplementation(() => {
      throw unknownError
    })

    await authenticate(mockReq as AuthRequest, mockRes as Response, mockNext)

    expect(mockNext).toHaveBeenCalledWith(unknownError)
  })
})
