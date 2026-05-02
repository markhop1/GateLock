import { beforeEach, describe, expect, it, vi } from 'vitest'
import { Request, Response } from 'express'
import { register, login, getMe } from '../auth.controller.js'
import type { AuthRequest } from '../../middleware/auth.middleware.js'

const { findOneMock, findByIdMock, saveMock, comparePasswordMock } = vi.hoisted(() => ({
  findOneMock: vi.fn(),
  findByIdMock: vi.fn(),
  saveMock: vi.fn(),
  comparePasswordMock: vi.fn(),
}))

vi.mock('../../models/User.model.js', () => {
  const UserMock: any = vi.fn().mockImplementation((data: Record<string, unknown>) => ({
    ...data,
    _id: { toString: () => 'user-id' },
    email: (data as any).email,
    name: (data as any).name,
    save: saveMock,
    comparePassword: comparePasswordMock,
  }))

  UserMock.findOne = findOneMock
  UserMock.findById = findByIdMock

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

  it('returns 400 when user already exists on register', async () => {
    findOneMock.mockResolvedValue({ _id: 'existing-id' })

    await register(mockReq as Request, mockRes as Response, mockNext)

    expect(mockRes.status).toHaveBeenCalledWith(400)
    expect(mockRes.json).toHaveBeenCalledWith({ error: 'A user with this email already exists' })
  })

  it('returns 201 with token on successful register', async () => {
    findOneMock.mockResolvedValue(null)
    saveMock.mockResolvedValue(undefined)

    await register(mockReq as Request, mockRes as Response, mockNext)

    expect(mockRes.status).toHaveBeenCalledWith(201)
    expect(mockRes.json).toHaveBeenCalledWith(
      expect.objectContaining({ token: 'mock-token' })
    )
  })
})

describe('Auth Controller - Login', () => {
  let mockReq: Partial<Request>
  let mockRes: Partial<Response>
  let mockNext: ReturnType<typeof vi.fn>

  const mockUser = {
    _id: { toString: () => 'user-id' },
    email: 'test@example.com',
    name: 'Test User',
    comparePassword: comparePasswordMock,
  }

  beforeEach(() => {
    mockReq = {
      body: { email: 'test@example.com', password: 'password123' },
    }
    mockRes = {
      status: vi.fn().mockReturnThis(),
      json: vi.fn().mockReturnThis(),
    }
    mockNext = vi.fn()
    vi.clearAllMocks()
  })

  it('returns 401 when user is not found', async () => {
    findOneMock.mockReturnValue({ select: vi.fn().mockResolvedValue(null) })

    await login(mockReq as Request, mockRes as Response, mockNext)

    expect(mockRes.status).toHaveBeenCalledWith(401)
    expect(mockRes.json).toHaveBeenCalledWith({ error: 'Invalid credentials' })
  })

  it('returns 401 when password is invalid', async () => {
    findOneMock.mockReturnValue({ select: vi.fn().mockResolvedValue(mockUser) })
    comparePasswordMock.mockResolvedValue(false)

    await login(mockReq as Request, mockRes as Response, mockNext)

    expect(mockRes.status).toHaveBeenCalledWith(401)
    expect(mockRes.json).toHaveBeenCalledWith({ error: 'Invalid credentials' })
  })

  it('returns token and user on successful login', async () => {
    findOneMock.mockReturnValue({ select: vi.fn().mockResolvedValue(mockUser) })
    comparePasswordMock.mockResolvedValue(true)

    await login(mockReq as Request, mockRes as Response, mockNext)

    expect(mockRes.json).toHaveBeenCalledWith(
      expect.objectContaining({ token: 'mock-token' })
    )
  })

  it('forwards errors to next in login', async () => {
    const err = new Error('db error')
    findOneMock.mockReturnValue({ select: vi.fn().mockRejectedValue(err) })

    await login(mockReq as Request, mockRes as Response, mockNext)

    expect(mockNext).toHaveBeenCalledWith(err)
  })
})

describe('Auth Controller - getMe', () => {
  let mockReq: Partial<AuthRequest>
  let mockRes: Partial<Response>
  let mockNext: ReturnType<typeof vi.fn>

  beforeEach(() => {
    mockReq = { userId: 'user-id' }
    mockRes = {
      status: vi.fn().mockReturnThis(),
      json: vi.fn().mockReturnThis(),
    }
    mockNext = vi.fn()
    vi.clearAllMocks()
  })

  it('returns 404 when user not found in getMe', async () => {
    findByIdMock.mockReturnValue({ select: vi.fn().mockResolvedValue(null) })

    await getMe(mockReq as AuthRequest, mockRes as Response, mockNext)

    expect(mockRes.status).toHaveBeenCalledWith(404)
    expect(mockRes.json).toHaveBeenCalledWith({ error: 'User not found' })
  })

  it('returns user data on successful getMe', async () => {
    const user = { _id: { toString: () => 'user-id' }, email: 'a@b.com', name: 'Alice' }
    findByIdMock.mockReturnValue({ select: vi.fn().mockResolvedValue(user) })

    await getMe(mockReq as AuthRequest, mockRes as Response, mockNext)

    expect(mockRes.json).toHaveBeenCalledWith({
      user: { id: 'user-id', email: 'a@b.com', name: 'Alice' },
    })
  })

  it('forwards errors to next in getMe', async () => {
    const err = new Error('db error')
    findByIdMock.mockReturnValue({ select: vi.fn().mockRejectedValue(err) })

    await getMe(mockReq as AuthRequest, mockRes as Response, mockNext)

    expect(mockNext).toHaveBeenCalledWith(err)
  })
})
