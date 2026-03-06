import { Response, NextFunction } from 'express'
import * as nukiService from '../services/nuki.service.js'
import { AuthRequest } from '../middleware/auth.middleware.js'

export const getLockStatus = async (
  _req: AuthRequest,
  res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    const result = await nukiService.getState()
    res.json(result)
  } catch (error) {
    next(error)
  }
}

export const setLockAction = async (
  req: AuthRequest,
  res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    const { action } = req.body
    if (action !== 'lock' && action !== 'unlock') {
      res.status(400).json({ error: 'Action must be "lock" or "unlock"' })
      return
    }

    if (action === 'lock') {
      await nukiService.lock()
    } else {
      await nukiService.unlock({ throwOnError: true })
    }

    res.json({ success: true, action })
  } catch (error) {
    next(error)
  }
}
