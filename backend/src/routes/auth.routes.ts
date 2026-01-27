import { Router } from 'express'
import { register, login, getMe } from '../controllers/auth.controller.js'
import { authenticate } from '../middleware/auth.middleware.js'

const router = Router()

// eslint-disable-next-line @typescript-eslint/no-explicit-any
router.post('/register', register as any)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
router.post('/login', login as any)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
router.get('/me', authenticate, getMe as any)

export default router
