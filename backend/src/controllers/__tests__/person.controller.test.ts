import { describe, it, expect, beforeEach, vi } from 'vitest'
import { Request, Response } from 'express'
import { createPerson } from '../person.controller.js'

// Mock Person model to prevent actual database calls
vi.mock('../../models/Person.model.js', () => ({
  Person: vi.fn().mockImplementation(() => ({
    save: vi.fn().mockResolvedValue(true),
    _id: { toString: () => '507f1f77bcf86cd799439011' },
    name: 'Test Person',
    email: 'test@example.com',
    createdAt: new Date(),
  })),
}))

describe('Person Controller - Validation', () => {
  let mockReq: Partial<Request>
  let mockRes: Partial<Response>
  let mockNext: ReturnType<typeof vi.fn>

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
    vi.clearAllMocks()
  })

  describe('createPerson - input validation', () => {
    it('should return 400 if name is missing', async () => {
      mockReq.body = { email: 'test@example.com' }

      await createPerson(mockReq as any, mockRes as Response, mockNext)

      expect(mockRes.status).toHaveBeenCalledWith(400)
      expect(mockRes.json).toHaveBeenCalledWith({
        error: 'Name is required',
      })
      expect(mockNext).not.toHaveBeenCalled()
    })
  })
})
