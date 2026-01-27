import express from 'express'
import cors from 'cors'
import dotenv from 'dotenv'
import { connectDB } from './config/database.js'
import authRoutes from './routes/auth.routes.js'
import personRoutes from './routes/person.routes.js'
import alertRoutes from './routes/alert.routes.js'
import { errorHandler } from './middleware/errorHandler.js'

// Load environment variables
dotenv.config()

const app = express()
const PORT = process.env.PORT || 5000

// Middleware - CORS configuration
const corsOptions: cors.CorsOptions = {
  origin: (origin: string | undefined, callback: (err: Error | null, allow?: boolean) => void) => {
    // Allow requests with no origin (like mobile apps, Postman, etc.)
    if (!origin) {
      callback(null, true)
      return
    }
    
    // In development, allow any localhost origin
    if (process.env.NODE_ENV === 'development' || !process.env.NODE_ENV) {
      if (origin.startsWith('http://localhost:') || origin.startsWith('http://127.0.0.1:')) {
        callback(null, true)
        return
      }
    }
    
    // In production, use configured CORS_ORIGIN
    const allowedOrigins = process.env.CORS_ORIGIN?.split(',').map(o => o.trim()) || ['http://localhost:3000']
    if (allowedOrigins.includes(origin)) {
      callback(null, true)
    } else {
      callback(new Error(`Not allowed by CORS. Origin: ${origin}`))
    }
  },
  credentials: true,
}

app.use(cors(corsOptions))
app.use(express.json())
app.use(express.urlencoded({ extended: true }))

// Health check
app.get('/api/health', (_req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() })
})

// Routes
app.use('/api/auth', authRoutes)
app.use('/api/persons', personRoutes)
app.use('/api/alerts', alertRoutes)

// Error handling middleware (must be last)
app.use(errorHandler)

// Start server
const startServer = async () => {
  try {
    // Connect to MongoDB
    await connectDB()
    
    app.listen(PORT, () => {
      console.log(`Server running on port ${PORT}`)
      console.log(`Environment: ${process.env.NODE_ENV || 'development'}`)
    })
  } catch (error) {
    console.error('Failed to start server:', error)
    process.exit(1)
  }
}

startServer()
