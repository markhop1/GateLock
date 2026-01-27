import { Router } from 'express'
import {
  createPerson,
  getPersons,
  getPersonById,
  updatePerson,
  deletePerson,
} from '../controllers/person.controller.js'
import { authenticate } from '../middleware/auth.middleware.js'

const router = Router()

// All routes require authentication
router.use(authenticate)

// eslint-disable-next-line @typescript-eslint/no-explicit-any
router.post('/', createPerson as any)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
router.get('/', getPersons as any)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
router.get('/:id', getPersonById as any)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
router.put('/:id', updatePerson as any)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
router.delete('/:id', deletePerson as any)

export default router
