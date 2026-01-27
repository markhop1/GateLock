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

router.post('/', createAlert)
router.get('/', getAlerts)
router.get('/:id', getAlertById)
router.patch('/:id/status', updateAlertStatus)

export default router
