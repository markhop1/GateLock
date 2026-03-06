import { Response, NextFunction } from 'express'
import mongoose from 'mongoose'
import { Alert, AlertStatus } from '../models/Alert.model.js'
import { Person } from '../models/Person.model.js'
import { AuthRequest } from '../middleware/auth.middleware.js'
import * as nukiService from '../services/nuki.service.js'

const EXPIRATION_TIME_MS = 5 * 60 * 1000 // 5 minutos

export const createAlert = async (
  req: AuthRequest,
  res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    const { personId, personName, videoUrl, message } = req.body
    const userId = req.userId!

    if (!personName || !videoUrl || !message) {
      res.status(400).json({
        error: 'personName, videoUrl, and message are required',
      })
      return
    }

    let finalPersonId: mongoose.Types.ObjectId

    // If personId is provided and is a valid ObjectId, try to use it
    if (personId && mongoose.Types.ObjectId.isValid(personId)) {
      const existingPerson = await Person.findOne({
        _id: personId,
        userId: new mongoose.Types.ObjectId(userId),
      })

      if (existingPerson) {
        finalPersonId = existingPerson._id
      } else {
        // Person doesn't exist, create a new one
        const newPerson = new Person({
          name: personName,
          userId: new mongoose.Types.ObjectId(userId),
        })
        await newPerson.save()
        finalPersonId = newPerson._id
      }
    } else {
      // personId is not valid or not provided, create or find person by name
      let person = await Person.findOne({
        name: personName.trim(),
        userId: new mongoose.Types.ObjectId(userId),
      })

      if (!person) {
        // Create new person
        person = new Person({
          name: personName.trim(),
          userId: new mongoose.Types.ObjectId(userId),
        })
        await person.save()
      }

      finalPersonId = person._id
    }

    const alert = new Alert({
      personId: finalPersonId,
      personName: personName.trim(),
      videoUrl,
      message,
      userId: new mongoose.Types.ObjectId(userId),
      timestamp: new Date(),
      status: 'pending',
    })

    await alert.save()

    res.status(201).json({
      alert: {
        id: alert._id.toString(),
        personId: alert.personId.toString(),
        personName: alert.personName,
        videoUrl: alert.videoUrl,
        message: alert.message,
        status: alert.status,
        timestamp: alert.timestamp,
      },
    })
  } catch (error) {
    next(error)
  }
}

export const getAlerts = async (
  req: AuthRequest,
  res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    const userId = req.userId!
    const { status } = req.query

    // Check and update expired alerts
    await checkExpiredAlerts(userId)

    interface AlertQuery {
      userId: mongoose.Types.ObjectId
      status?: AlertStatus
    }

    const query: AlertQuery = { userId: new mongoose.Types.ObjectId(userId) }
    if (status) {
      query.status = status as AlertStatus
    }

    const alerts = await Alert.find(query)
      .sort({ timestamp: -1 })
      .lean()

    res.json({
      alerts: alerts.map((alert) => ({
        id: alert._id.toString(),
        personId: alert.personId.toString(),
        personName: alert.personName,
        videoUrl: alert.videoUrl,
        message: alert.message,
        status: alert.status,
        timestamp: alert.timestamp,
        decisionTimestamp: alert.decisionTimestamp,
      })),
    })
  } catch (error) {
    next(error)
  }
}

export const getAlertById = async (
  req: AuthRequest,
  res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    const { id } = req.params
    const userId = req.userId!

    const alert = await Alert.findOne({ _id: id, userId }).lean()

    if (!alert) {
      res.status(404).json({ error: 'Alert not found' })
      return
    }

    res.json({
      alert: {
        id: alert._id.toString(),
        personId: alert.personId.toString(),
        personName: alert.personName,
        videoUrl: alert.videoUrl,
        message: alert.message,
        status: alert.status,
        timestamp: alert.timestamp,
        decisionTimestamp: alert.decisionTimestamp,
      },
    })
  } catch (error) {
    next(error)
  }
}

export const updateAlertStatus = async (
  req: AuthRequest,
  res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    const { id } = req.params
    const { status } = req.body
    const userId = req.userId!

    if (!['accepted', 'ignored'].includes(status)) {
      res.status(400).json({
        error: 'Status must be either "accepted" or "ignored"',
      })
      return
    }

    const alert = await Alert.findOne({ _id: id, userId })

    if (!alert) {
      res.status(404).json({ error: 'Alert not found' })
      return
    }

    if (alert.status !== 'pending') {
      res.status(400).json({ error: 'Alert has already been processed' })
      return
    }

    alert.status = status as 'accepted' | 'ignored'
    alert.decisionTimestamp = new Date()

    await alert.save()

    if (status === 'accepted') {
      void nukiService.unlock()
    }

    res.json({
      alert: {
        id: alert._id.toString(),
        personId: alert.personId.toString(),
        personName: alert.personName,
        videoUrl: alert.videoUrl,
        message: alert.message,
        status: alert.status,
        timestamp: alert.timestamp,
        decisionTimestamp: alert.decisionTimestamp,
      },
    })
  } catch (error) {
    next(error)
  }
}

// Helper function to check and update expired alerts
const checkExpiredAlerts = async (userId: string): Promise<void> => {
  const now = new Date()
  const expiredThreshold = new Date(now.getTime() - EXPIRATION_TIME_MS)

  await Alert.updateMany(
    {
      userId: new mongoose.Types.ObjectId(userId),
      status: 'pending',
      timestamp: { $lt: expiredThreshold },
    },
    {
      status: 'unanswered',
      decisionTimestamp: now,
    }
  )
}
