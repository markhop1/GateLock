import { Response, NextFunction } from 'express'
import { Person } from '../models/Person.model.js'
import { Alert } from '../models/Alert.model.js'
import { AuthRequest } from '../middleware/auth.middleware.js'

export const createPerson = async (
  req: AuthRequest,
  res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    const { name, email, photoUrl } = req.body
    const userId = req.userId!

    if (!name) {
      res.status(400).json({ error: 'Name is required' })
      return
    }

    const person = new Person({
      name,
      email,
      photoUrl,
      userId,
    })

    await person.save()

    res.status(201).json({
      person: {
        id: person._id.toString(),
        name: person.name,
        email: person.email,
        photoUrl: person.photoUrl,
        createdAt: person.createdAt,
      },
    })
  } catch (error) {
    next(error)
  }
}

export const getPersons = async (
  req: AuthRequest,
  res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    const userId = req.userId!

    const persons = await Person.find({ userId }).sort({ createdAt: -1 })

    res.json({
      persons: persons.map((person) => ({
        id: person._id.toString(),
        name: person.name,
        email: person.email,
        photoUrl: person.photoUrl,
        createdAt: person.createdAt,
      })),
    })
  } catch (error) {
    next(error)
  }
}

export const getPersonById = async (
  req: AuthRequest,
  res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    const { id } = req.params
    const userId = req.userId!

    const person = await Person.findOne({ _id: id, userId })

    if (!person) {
      res.status(404).json({ error: 'Person not found' })
      return
    }

    res.json({
      person: {
        id: person._id.toString(),
        name: person.name,
        email: person.email,
        photoUrl: person.photoUrl,
        createdAt: person.createdAt,
      },
    })
  } catch (error) {
    next(error)
  }
}

export const updatePerson = async (
  req: AuthRequest,
  res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    const { id } = req.params
    const { name, email, photoUrl } = req.body
    const userId = req.userId!

    const person = await Person.findOne({ _id: id, userId })

    if (!person) {
      res.status(404).json({ error: 'Person not found' })
      return
    }

    const nameChanged = name && typeof name === 'string' && name.trim() !== person.name.trim()

    if (name && typeof name === 'string') {
      person.name = name.trim()
    }
    if (email !== undefined) person.email = email
    if (photoUrl !== undefined) person.photoUrl = photoUrl

    await person.save()

    // If name changed, update all related alerts
    if (nameChanged) {
      await Alert.updateMany(
        { personId: person._id, userId },
        { personName: person.name }
      )
    }

    res.json({
      person: {
        id: person._id.toString(),
        name: person.name,
        email: person.email,
        photoUrl: person.photoUrl,
        createdAt: person.createdAt,
        updatedAt: person.updatedAt,
      },
    })
  } catch (error) {
    next(error)
  }
}

export const deletePerson = async (
  req: AuthRequest,
  res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    const { id } = req.params
    const userId = req.userId!

    const person = await Person.findOneAndDelete({ _id: id, userId })

    if (!person) {
      res.status(404).json({ error: 'Person not found' })
      return
    }

    res.json({ message: 'Person deleted successfully' })
  } catch (error) {
    next(error)
  }
}
