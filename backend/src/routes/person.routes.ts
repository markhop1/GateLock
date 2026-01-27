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

router.post('/', createPerson)
router.get('/', getPersons)
router.get('/:id', getPersonById)
router.put('/:id', updatePerson)
router.delete('/:id', deletePerson)

export default router
