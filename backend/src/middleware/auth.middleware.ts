import { Request, Response, NextFunction } from 'express'
import jwt from 'jsonwebtoken'
import { User } from '../models/User.model.js'

export interface AuthRequest extends Request {
  userId?: string
  user?: {
    id: string
    email: string
    name: string
  }
}

export const authenticate = async (
  req: AuthRequest,
  res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    const token = req.headers.authorization?.replace('Bearer ', '')

    if (!token) {
      res.status(401).json({ error: 'Authentication required' })
      return
    }

    const jwtSecret = process.env.JWT_SECRET
    if (!jwtSecret) {
      res.status(500).json({ error: 'Server configuration error' })
      return
    }

    const decoded = jwt.verify(token, jwtSecret) as { userId: string }
    
    const user = await User.findById(decoded.userId).select('-password')
    
    if (!user) {
      res.status(401).json({ error: 'User not found' })
      return
    }

    req.userId = user._id.toString()
    req.user = {
      id: user._id.toString(),
      email: user.email,
      name: user.name,
    }

    next()
  } catch (error) {
    if (error instanceof jwt.JsonWebTokenError) {
      res.status(401).json({ error: 'Invalid token' })
      return
    }
    next(error)
  }
}
