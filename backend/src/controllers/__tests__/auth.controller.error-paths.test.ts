import { beforeEach, describe, expect, it, vi } from 'vitest'
import { Request, Response } from 'express'
import { register } from '../auth.controller.js'

const { findOneMock, saveMock } = vi.hoisted(() => ({
  findOneMock: vi.fn(),
  saveMock: vi.fn(),
}))

vi.mock('../../models/User.model.js', () => {
  const UserMock: any = vi.fn().mockImplementation((data: Record<string, unknown>) => ({
    ...data,
    _id: { toString: () => 'user-id' },
    save: saveMock,
  }))

  UserMock.findOne = findOneMock

  return {
    User: UserMock,
  }
})

vi.mock('../../utils/jwt.js', () => ({
  generateToken: vi.fn(() => 'mock-token'),
}))

describe('Auth Controller - Error Paths', () => {
  let mockReq: Partial<Request>
  let mockRes: Partial<Response>
  let mockNext: ReturnType<typeof vi.fn>

  beforeEach(() => {
    mockReq = {
      body: {
        email: 'test@example.com',
        password: 'password123',
        name: 'Test User',
      },
    }
    mockRes = {
      status: vi.fn().mockReturnThis(),
      json: vi.fn().mockReturnThis(),
    }
    mockNext = vi.fn()

    vi.clearAllMocks()
    findOneMock.mockResolvedValue(null)
  })

  it('returns 400 for mongoose validation errors from save', async () => {
    saveMock.mockRejectedValue({
      name: 'ValidationError',
      errors: {
        email: { message: 'Email is required' },
        password: { message: 'Password is required' },
      },
    })

    await register(mockReq as Request, mockRes as Response, mockNext)

    expect(mockRes.status).toHaveBeenCalledWith(400)
    expect(mockRes.json).toHaveBeenCalledWith({
      error: 'Email is required, Password is required',
    })
    expect(mockNext).not.toHaveBeenCalled()
  })

  it('returns 400 for duplicate key errors from save', async () => {
    saveMock.mockRejectedValue({ code: 11000 })

    await register(mockReq as Request, mockRes as Response, mockNext)

    expect(mockRes.status).toHaveBeenCalledWith(400)
    expect(mockRes.json).toHaveBeenCalledWith({
      error: 'A user with this email already exists',
    })
    expect(mockNext).not.toHaveBeenCalled()
  })

  it('forwards unknown errors to next', async () => {
    const unknownError = new Error('Unexpected DB error')
    saveMock.mockRejectedValue(unknownError)

    await register(mockReq as Request, mockRes as Response, mockNext)

    expect(mockNext).toHaveBeenCalledWith(unknownError)
  })
})
