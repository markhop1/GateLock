import { Request, Response, NextFunction } from 'express'
import mongoose from 'mongoose'

export interface AppError extends Error {
  statusCode?: number
  code?: number
  keyPattern?: Record<string, unknown>
}

export const errorHandler = (
  err: AppError,
  _req: Request,
  res: Response,
  _next: NextFunction
): void => {
  let statusCode = err.statusCode || 500
  let message = err.message || 'Internal Server Error'

  // Mongoose validation error
  if (err instanceof mongoose.Error.ValidationError) {
    statusCode = 400
    const errors = Object.values(err.errors).map((e) => e.message)
    message = errors.join(', ')
  }

  // Mongoose duplicate key error
  if (err.code === 11000 && err.keyPattern) {
    statusCode = 400
    const field = Object.keys(err.keyPattern)[0]
    message = `${field} already exists`
  }

  // Mongoose cast error (invalid ObjectId)
  if (err instanceof mongoose.Error.CastError) {
    statusCode = 400
    message = 'Invalid ID format'
  }

  // JWT errors
  if (err.name === 'JsonWebTokenError') {
    statusCode = 401
    message = 'Invalid token'
  }

  if (err.name === 'TokenExpiredError') {
    statusCode = 401
    message = 'Token expired'
  }

  res.status(statusCode).json({
    error: message,
    ...(process.env.NODE_ENV === 'development' && { stack: err.stack }),
  })
}
