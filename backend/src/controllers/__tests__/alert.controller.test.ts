import { describe, it, expect, beforeEach, vi } from 'vitest'
import { Request, Response } from 'express'
import { createAlert, updateAlertStatus } from '../alert.controller.js'

// Mock models to prevent actual database calls
vi.mock('../../models/Person.model.js', () => ({
  Person: {
    findOne: vi.fn(),
  },
}))

vi.mock('../../models/Alert.model.js', () => ({
  Alert: {
    findOne: vi.fn(),
  },
}))

describe('Alert Controller - Validation', () => {
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

  describe('createAlert - input validation', () => {
    it('should return 400 if personName is missing', async () => {
      mockReq.body = {
        videoUrl: 'https://example.com/video.mp4',
        message: 'Test message',
      }

      await createAlert(mockReq as any, mockRes as Response, mockNext)

      expect(mockRes.status).toHaveBeenCalledWith(400)
      expect(mockRes.json).toHaveBeenCalledWith({
        error: 'personName, videoUrl, and message are required',
      })
      expect(mockNext).not.toHaveBeenCalled()
    })

    it('should return 400 if videoUrl is missing', async () => {
      mockReq.body = {
        personName: 'Test Person',
        message: 'Test message',
      }

      await createAlert(mockReq as any, mockRes as Response, mockNext)

      expect(mockRes.status).toHaveBeenCalledWith(400)
      expect(mockRes.json).toHaveBeenCalledWith({
        error: 'personName, videoUrl, and message are required',
      })
      expect(mockNext).not.toHaveBeenCalled()
    })

    it('should return 400 if message is missing', async () => {
      mockReq.body = {
        personName: 'Test Person',
        videoUrl: 'https://example.com/video.mp4',
      }

      await createAlert(mockReq as any, mockRes as Response, mockNext)

      expect(mockRes.status).toHaveBeenCalledWith(400)
      expect(mockRes.json).toHaveBeenCalledWith({
        error: 'personName, videoUrl, and message are required',
      })
      expect(mockNext).not.toHaveBeenCalled()
    })
  })

  describe('updateAlertStatus - input validation', () => {
    it('should return 400 if status is invalid', async () => {
      mockReq.params = { id: 'alert-id' }
      mockReq.body = { status: 'invalid-status' }

      await updateAlertStatus(mockReq as any, mockRes as Response, mockNext)

      expect(mockRes.status).toHaveBeenCalledWith(400)
      expect(mockRes.json).toHaveBeenCalledWith({
        error: 'Status must be either "accepted" or "ignored"',
      })
      expect(mockNext).not.toHaveBeenCalled()
    })

    it('should return 400 if status is missing', async () => {
      mockReq.params = { id: 'alert-id' }
      mockReq.body = {}

      await updateAlertStatus(mockReq as any, mockRes as Response, mockNext)

      expect(mockRes.status).toHaveBeenCalledWith(400)
      expect(mockRes.json).toHaveBeenCalledWith({
        error: 'Status must be either "accepted" or "ignored"',
      })
      expect(mockNext).not.toHaveBeenCalled()
    })
  })
})
