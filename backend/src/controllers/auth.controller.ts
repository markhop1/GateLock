import { Response, NextFunction } from 'express'
import { User } from '../models/User.model.js'
import { generateToken } from '../utils/jwt.js'
import { AuthRequest } from '../middleware/auth.middleware.js'

export const register = async (
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    const { email, password, name } = req.body

    // Validation
    if (!email || !password || !name) {
      res.status(400).json({ error: 'Email, password, and name are required' })
      return
    }

    // Trim and validate email format
    const trimmedEmail = email.trim().toLowerCase()
    if (!trimmedEmail || !trimmedEmail.includes('@')) {
      res.status(400).json({ error: 'Please provide a valid email address' })
      return
    }

    // Validate password length
    if (password.length < 6) {
      res.status(400).json({ error: 'Password must be at least 6 characters long' })
      return
    }

    // Validate name
    const trimmedName = name.trim()
    if (!trimmedName || trimmedName.length < 2) {
      res.status(400).json({ error: 'Name must be at least 2 characters long' })
      return
    }

    // Check if user already exists
    const existingUser = await User.findOne({ email: trimmedEmail })
    if (existingUser) {
      res.status(400).json({ error: 'A user with this email already exists' })
      return
    }

    // Create user
    const user = new User({
      email: trimmedEmail,
      password,
      name: trimmedName,
    })

    await user.save()

    // Generate token
    const token = generateToken(user._id.toString())

    res.status(201).json({
      token,
      user: {
        id: user._id.toString(),
        email: user.email,
        name: user.name,
      },
    })
  } catch (error: unknown) {
    // Handle mongoose validation errors
    if (error && typeof error === 'object' && 'name' in error && error.name === 'ValidationError' && 'errors' in error) {
      const validationError = error as { errors: Record<string, { message: string }> }
      const messages = Object.values(validationError.errors).map((err) => err.message)
      res.status(400).json({ error: messages.join(', ') })
      return
    }
    
    // Handle duplicate key error (email already exists)
    if (error && typeof error === 'object' && 'code' in error && error.code === 11000) {
      res.status(400).json({ error: 'A user with this email already exists' })
      return
    }
    
    // Pass other errors to error handler
    next(error)
  }
}

export const login = async (
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    const { email, password } = req.body

    // Validation
    if (!email || !password) {
      res.status(400).json({ error: 'Email and password are required' })
      return
    }

    // Find user and include password
    const user = await User.findOne({ email }).select('+password')
    
    if (!user) {
      res.status(401).json({ error: 'Invalid credentials' })
      return
    }

    // Check password
    const isPasswordValid = await user.comparePassword(password)
    
    if (!isPasswordValid) {
      res.status(401).json({ error: 'Invalid credentials' })
      return
    }

    // Generate token
    const token = generateToken(user._id.toString())

    res.json({
      token,
      user: {
        id: user._id.toString(),
        email: user.email,
        name: user.name,
      },
    })
  } catch (error) {
    next(error)
  }
}

export const getMe = async (
  req: AuthRequest,
  res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    const user = await User.findById(req.userId).select('-password')
    
    if (!user) {
      res.status(404).json({ error: 'User not found' })
      return
    }

    res.json({
      user: {
        id: user._id.toString(),
        email: user.email,
        name: user.name,
      },
    })
  } catch (error) {
    next(error)
  }
}
