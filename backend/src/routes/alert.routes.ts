import { Router } from 'express'
import {
  createAlert,
  getAlerts,
  getAlertById,
  updateAlertStatus,
} from '../controllers/alert.controller.js'
import { authenticate } from '../middleware/auth.middleware.js'

const router = Router()

// All routes require authentication
router.use(authenticate)

// eslint-disable-next-line @typescript-eslint/no-explicit-any
router.post('/', createAlert as any)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
router.get('/', getAlerts as any)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
router.get('/:id', getAlertById as any)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
router.patch('/:id/status', updateAlertStatus as any)

export default router
