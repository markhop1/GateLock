import { Router } from 'express'
import { getLockStatus, setLockAction } from '../controllers/nuki.controller.js'
import { authenticate } from '../middleware/auth.middleware.js'

const router = Router()

router.use(authenticate)

// eslint-disable-next-line @typescript-eslint/no-explicit-any
router.get('/status', getLockStatus as any)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
router.post('/action', setLockAction as any)

export default router
