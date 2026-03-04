import { describe, it, expect, beforeEach, vi } from 'vitest'
import { Response } from 'express'
import {
  createPerson,
  getPersons,
  getPersonById,
  updatePerson,
  deletePerson,
} from '../person.controller.js'
import { AuthRequest } from '../../middleware/auth.middleware.js'
import { Person } from '../../models/Person.model.js'
import { Alert } from '../../models/Alert.model.js'

vi.mock('../../models/Person.model.js', () => {
  const PersonConstructor = vi.fn().mockImplementation((opts: { name?: string; email?: string }) => ({
    _id: { toString: () => '507f1f77bcf86cd799439011' },
    name: opts?.name ?? 'Test',
    email: opts?.email,
    photoUrl: opts?.photoUrl,
    createdAt: new Date(),
    updatedAt: new Date(),
    save: vi.fn().mockResolvedValue(undefined),
  }))
  Object.assign(PersonConstructor, {
    find: vi.fn(),
    findOne: vi.fn(),
    findOneAndDelete: vi.fn(),
  })
  return { Person: PersonConstructor }
})

vi.mock('../../models/Alert.model.js', () => ({
  Alert: {
    updateMany: vi.fn(),
  },
}))

describe('Person Controller', () => {
  let mockReq: Partial<AuthRequest>
  let mockRes: Partial<Response>
  let mockNext: ReturnType<typeof vi.fn>
  let mockPersonInstance: {
    _id: { toString: () => string }
    name: string
    email?: string
    photoUrl?: string
    createdAt: Date
    updatedAt?: Date
    save: ReturnType<typeof vi.fn>
  }

  beforeEach(() => {
    mockReq = {
      body: {},
      params: {},
      userId: 'user-id-123',
    }
    mockRes = {
      status: vi.fn().mockReturnThis(),
      json: vi.fn().mockReturnThis(),
    }
    mockNext = vi.fn()
    mockPersonInstance = {
      _id: { toString: () => '507f1f77bcf86cd799439011' },
      name: 'Test Person',
      email: 'test@example.com',
      createdAt: new Date(),
      save: vi.fn().mockResolvedValue(undefined),
    }
    vi.clearAllMocks()
  })

  describe('createPerson', () => {
    it('should return 400 if name is missing', async () => {
      mockReq.body = { email: 'test@example.com' }

      await createPerson(mockReq as AuthRequest, mockRes as Response, mockNext)

      expect(mockRes.status).toHaveBeenCalledWith(400)
      expect(mockRes.json).toHaveBeenCalledWith({ error: 'Name is required' })
      expect(mockNext).not.toHaveBeenCalled()
    })

    it('should create person and return 201 on success', async () => {
      mockReq.body = { name: 'Juan', email: 'juan@test.com' }
      const personInstance = {
        _id: { toString: () => '507f1f77bcf86cd799439011' },
        name: 'Juan',
        email: 'juan@test.com',
        photoUrl: undefined,
        createdAt: new Date(),
        save: vi.fn().mockResolvedValue(undefined),
      }
      vi.mocked(Person).mockImplementation(() => personInstance as never)

      await createPerson(mockReq as AuthRequest, mockRes as Response, mockNext)

      expect(Person).toHaveBeenCalledWith({
        name: 'Juan',
        email: 'juan@test.com',
        photoUrl: undefined,
        userId: 'user-id-123',
      })
      expect(mockRes.status).toHaveBeenCalledWith(201)
      expect(mockRes.json).toHaveBeenCalledWith(
        expect.objectContaining({
          person: expect.objectContaining({
            id: '507f1f77bcf86cd799439011',
            name: 'Juan',
            email: 'juan@test.com',
          }),
        })
      )
      expect(mockNext).not.toHaveBeenCalled()
    })
  })

  describe('getPersons', () => {
    it('should return persons for the user', async () => {
      const mockPersons = [
        {
          _id: { toString: () => '1' },
          name: 'Person 1',
          email: 'p1@test.com',
          photoUrl: undefined,
          createdAt: new Date(),
        },
      ]
      vi.mocked(Person.find).mockReturnValue({
        sort: vi.fn().mockResolvedValue(mockPersons),
      } as never)

      await getPersons(mockReq as AuthRequest, mockRes as Response, mockNext)

      expect(Person.find).toHaveBeenCalledWith({ userId: 'user-id-123' })
      expect(mockRes.json).toHaveBeenCalledWith({
        persons: expect.arrayContaining([
          expect.objectContaining({
            id: '1',
            name: 'Person 1',
            email: 'p1@test.com',
          }),
        ]),
      })
      expect(mockNext).not.toHaveBeenCalled()
    })
  })

  describe('getPersonById', () => {
    it('should return 404 if person not found', async () => {
      mockReq.params = { id: 'nonexistent' }
      vi.mocked(Person.findOne).mockResolvedValue(null)

      await getPersonById(mockReq as AuthRequest, mockRes as Response, mockNext)

      expect(mockRes.status).toHaveBeenCalledWith(404)
      expect(mockRes.json).toHaveBeenCalledWith({ error: 'Person not found' })
      expect(mockNext).not.toHaveBeenCalled()
    })

    it('should return person when found', async () => {
      mockReq.params = { id: '507f1f77bcf86cd799439011' }
      const mockPerson = {
        _id: { toString: () => '507f1f77bcf86cd799439011' },
        name: 'Found Person',
        email: 'found@test.com',
        photoUrl: 'https://photo.jpg',
        createdAt: new Date(),
      }
      vi.mocked(Person.findOne).mockResolvedValue(mockPerson as never)

      await getPersonById(mockReq as AuthRequest, mockRes as Response, mockNext)

      expect(mockRes.json).toHaveBeenCalledWith({
        person: expect.objectContaining({
          id: '507f1f77bcf86cd799439011',
          name: 'Found Person',
          email: 'found@test.com',
        }),
      })
      expect(mockNext).not.toHaveBeenCalled()
    })
  })

  describe('updatePerson', () => {
    it('should return 404 if person not found', async () => {
      mockReq.params = { id: 'nonexistent' }
      mockReq.body = { name: 'Updated' }
      vi.mocked(Person.findOne).mockResolvedValue(null)

      await updatePerson(mockReq as AuthRequest, mockRes as Response, mockNext)

      expect(mockRes.status).toHaveBeenCalledWith(404)
      expect(mockRes.json).toHaveBeenCalledWith({ error: 'Person not found' })
      expect(mockNext).not.toHaveBeenCalled()
    })

    it('should update and return person when found', async () => {
      mockReq.params = { id: '507f1f77bcf86cd799439011' }
      mockReq.body = { name: 'Updated Name' }
      const updatedPerson = {
        _id: { toString: () => '507f1f77bcf86cd799439011' },
        name: 'Old Name',
        email: 'test@test.com',
        photoUrl: undefined,
        createdAt: new Date(),
        updatedAt: new Date(),
        save: vi.fn().mockResolvedValue(undefined),
      }
      vi.mocked(Person.findOne).mockResolvedValue(updatedPerson as never)
      vi.mocked(Alert.updateMany).mockResolvedValue({ modifiedCount: 1 } as never)

      await updatePerson(mockReq as AuthRequest, mockRes as Response, mockNext)

      expect(updatedPerson.name).toBe('Updated Name')
      expect(mockRes.json).toHaveBeenCalledWith(
        expect.objectContaining({
          person: expect.objectContaining({
            name: 'Updated Name',
          }),
        })
      )
      expect(mockNext).not.toHaveBeenCalled()
    })
  })

  describe('deletePerson', () => {
    it('should return 404 if person not found', async () => {
      mockReq.params = { id: 'nonexistent' }
      vi.mocked(Person.findOneAndDelete).mockResolvedValue(null)

      await deletePerson(mockReq as AuthRequest, mockRes as Response, mockNext)

      expect(mockRes.status).toHaveBeenCalledWith(404)
      expect(mockNext).not.toHaveBeenCalled()
    })

    it('should return success message when person deleted', async () => {
      mockReq.params = { id: '507f1f77bcf86cd799439011' }
      const deletedPerson = {
        _id: { toString: () => '507f1f77bcf86cd799439011' },
        name: 'Deleted',
      }
      vi.mocked(Person.findOneAndDelete).mockResolvedValue(deletedPerson as never)

      await deletePerson(mockReq as AuthRequest, mockRes as Response, mockNext)

      expect(mockRes.json).toHaveBeenCalledWith({
        message: 'Person deleted successfully',
      })
      expect(mockNext).not.toHaveBeenCalled()
    })
  })
})
