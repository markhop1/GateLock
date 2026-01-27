import { describe, it, expect, vi, beforeEach } from 'vitest'
import { Request, Response } from 'express'
import { errorHandler, AppError } from '../errorHandler.js'
import mongoose from 'mongoose'

describe('Error Handler', () => {
  let mockReq: Partial<Request>
  let mockRes: Partial<Response>
  let mockNext: ReturnType<typeof vi.fn>

  beforeEach(() => {
    mockReq = {}
    mockRes = {
      status: vi.fn().mockReturnThis(),
      json: vi.fn().mockReturnThis(),
    }
    mockNext = vi.fn()
    vi.clearAllMocks()
  })

  it('should handle mongoose validation errors', () => {
    const validationError = new mongoose.Error.ValidationError()
    validationError.errors = {
      email: {
        message: 'Email is required',
        name: 'ValidatorError',
        path: 'email',
        value: undefined,
      } as any,
    }

    errorHandler(validationError as AppError, mockReq as Request, mockRes as Response, mockNext)

    expect(mockRes.status).toHaveBeenCalledWith(400)
    expect(mockRes.json).toHaveBeenCalledWith({
      error: 'Email is required',
    })
  })

  it('should handle duplicate key errors', () => {
    const duplicateError: AppError = {
      name: 'MongoError',
      message: 'Duplicate key',
      code: 11000,
      keyPattern: {
        email: 1,
      },
    } as any

    errorHandler(duplicateError, mockReq as Request, mockRes as Response, mockNext)

    expect(mockRes.status).toHaveBeenCalledWith(400)
    expect(mockRes.json).toHaveBeenCalledWith({
      error: 'email already exists',
    })
  })

  it('should handle cast errors', () => {
    const castError = new mongoose.Error.CastError('ObjectId', 'invalid-id', 'id')

    errorHandler(castError as AppError, mockReq as Request, mockRes as Response, mockNext)

    expect(mockRes.status).toHaveBeenCalledWith(400)
    expect(mockRes.json).toHaveBeenCalledWith({
      error: 'Invalid ID format',
    })
  })

  it('should handle JWT errors', () => {
    const jwtError: AppError = {
      name: 'JsonWebTokenError',
      message: 'Invalid token',
    }

    errorHandler(jwtError, mockReq as Request, mockRes as Response, mockNext)

    expect(mockRes.status).toHaveBeenCalledWith(401)
    expect(mockRes.json).toHaveBeenCalledWith({
      error: 'Invalid token',
    })
  })

  it('should handle expired token errors', () => {
    const expiredError: AppError = {
      name: 'TokenExpiredError',
      message: 'Token expired',
    }

    errorHandler(expiredError, mockReq as Request, mockRes as Response, mockNext)

    expect(mockRes.status).toHaveBeenCalledWith(401)
    expect(mockRes.json).toHaveBeenCalledWith({
      error: 'Token expired',
    })
  })

  it('should handle generic errors with default status 500', () => {
    const genericError: AppError = {
      name: 'Error',
      message: 'Something went wrong',
    }

    errorHandler(genericError, mockReq as Request, mockRes as Response, mockNext)

    expect(mockRes.status).toHaveBeenCalledWith(500)
    expect(mockRes.json).toHaveBeenCalledWith({
      error: 'Something went wrong',
    })
  })
})
