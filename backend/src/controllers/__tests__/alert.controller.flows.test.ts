import { beforeEach, describe, expect, it, vi } from 'vitest'
import mongoose from 'mongoose'
import { Response } from 'express'
import {
  createAlert,
  getAlertById,
  getAlerts,
  updateAlertStatus,
} from '../alert.controller.js'
import { AuthRequest } from '../../middleware/auth.middleware.js'

const mocks = vi.hoisted(() => ({
  alertSaveMock: vi.fn(),
  alertFindMock: vi.fn(),
  alertFindOneMock: vi.fn(),
  alertUpdateManyMock: vi.fn(),
  alertSortMock: vi.fn(),
  alertLeanMock: vi.fn(),
  personFindOneMock: vi.fn(),
  personSaveMock: vi.fn(),
  unlockMock: vi.fn(),
}))

vi.mock('../../models/Alert.model.js', () => {
  const AlertMock = vi.fn().mockImplementation((data: Record<string, unknown>) => ({
    ...data,
    _id: new mongoose.Types.ObjectId(),
    save: mocks.alertSaveMock,
  }))

  ;(AlertMock as unknown as Record<string, unknown>).find = mocks.alertFindMock
  ;(AlertMock as unknown as Record<string, unknown>).findOne = mocks.alertFindOneMock
  ;(AlertMock as unknown as Record<string, unknown>).updateMany = mocks.alertUpdateManyMock

  return { Alert: AlertMock }
})

vi.mock('../../models/Person.model.js', () => {
  const PersonMock = vi.fn().mockImplementation((data: Record<string, unknown>) => ({
    ...data,
    _id: new mongoose.Types.ObjectId(),
    save: mocks.personSaveMock,
  }))

  ;(PersonMock as unknown as Record<string, unknown>).findOne = mocks.personFindOneMock

  return { Person: PersonMock }
})

vi.mock('../../services/nuki.service.js', () => ({
  unlock: mocks.unlockMock,
}))

describe('Alert Controller - Flow Coverage', () => {
  let mockReq: Partial<AuthRequest>
  let mockRes: Partial<Response>
  let mockNext: ReturnType<typeof vi.fn>

  beforeEach(() => {
    mockReq = {
      body: {},
      params: {},
      query: {},
      userId: '507f1f77bcf86cd799439011',
    }
    mockRes = {
      status: vi.fn().mockReturnThis(),
      json: vi.fn().mockReturnThis(),
    }
    mockNext = vi.fn()

    vi.clearAllMocks()
    mocks.alertUpdateManyMock.mockResolvedValue({})
  })

  it('creates alert with existing person by valid personId', async () => {
    const existingPersonId = new mongoose.Types.ObjectId()
    mocks.personFindOneMock.mockResolvedValue({ _id: existingPersonId })
    mocks.alertSaveMock.mockResolvedValue(undefined)

    mockReq.body = {
      personId: existingPersonId.toString(),
      personName: 'Visitor One',
      videoUrl: '/uploads/v1.mp4',
      message: 'Wants to enter',
    }

    await createAlert(mockReq as AuthRequest, mockRes as Response, mockNext)

    expect(mocks.personFindOneMock).toHaveBeenCalled()
    expect(mockRes.status).toHaveBeenCalledWith(201)
    expect(mockRes.json).toHaveBeenCalledWith(
      expect.objectContaining({
        alert: expect.objectContaining({
          personId: existingPersonId.toString(),
          personName: 'Visitor One',
          status: 'pending',
        }),
      })
    )
  })

  it('creates person when no personId is provided and person does not exist by name', async () => {
    mocks.personFindOneMock.mockResolvedValue(null)
    mocks.personSaveMock.mockResolvedValue(undefined)
    mocks.alertSaveMock.mockResolvedValue(undefined)

    mockReq.body = {
      personName: '  New Visitor  ',
      videoUrl: '/uploads/v2.mp4',
      message: 'Please open',
    }

    await createAlert(mockReq as AuthRequest, mockRes as Response, mockNext)

    expect(mocks.personFindOneMock).toHaveBeenCalled()
    expect(mocks.personSaveMock).toHaveBeenCalledTimes(1)
    expect(mockRes.status).toHaveBeenCalledWith(201)
  })

  it('lists alerts and maps output with expiration check', async () => {
    const personId = new mongoose.Types.ObjectId()
    const alertId = new mongoose.Types.ObjectId()
    const timestamp = new Date()

    mocks.alertFindMock.mockReturnValue({ sort: mocks.alertSortMock })
    mocks.alertSortMock.mockReturnValue({ lean: mocks.alertLeanMock })
    mocks.alertLeanMock.mockResolvedValue([
      {
        _id: alertId,
        personId,
        personName: 'Visitor',
        videoUrl: '/uploads/v.mp4',
        message: 'Open please',
        status: 'pending',
        timestamp,
        decisionTimestamp: undefined,
      },
    ])

    mockReq.query = { status: 'pending' }

    await getAlerts(mockReq as AuthRequest, mockRes as Response, mockNext)

    expect(mocks.alertUpdateManyMock).toHaveBeenCalledTimes(1)
    expect(mocks.alertFindMock).toHaveBeenCalledTimes(1)
    expect(mockRes.json).toHaveBeenCalledWith(
      expect.objectContaining({
        alerts: [
          expect.objectContaining({
            id: alertId.toString(),
            personId: personId.toString(),
            status: 'pending',
          }),
        ],
      })
    )
  })

  it('returns 404 when getAlertById cannot find alert', async () => {
    mocks.alertFindOneMock.mockReturnValue({
      lean: vi.fn().mockResolvedValue(null),
    })

    mockReq.params = { id: 'missing-alert' }

    await getAlertById(mockReq as AuthRequest, mockRes as Response, mockNext)

    expect(mockRes.status).toHaveBeenCalledWith(404)
    expect(mockRes.json).toHaveBeenCalledWith({ error: 'Alert not found' })
  })

  it('returns 400 when alert is already processed', async () => {
    mocks.alertFindOneMock.mockResolvedValue({ status: 'accepted' })
    mockReq.params = { id: 'alert-id' }
    mockReq.body = { status: 'accepted' }

    await updateAlertStatus(mockReq as AuthRequest, mockRes as Response, mockNext)

    expect(mockRes.status).toHaveBeenCalledWith(400)
    expect(mockRes.json).toHaveBeenCalledWith({ error: 'Alert has already been processed' })
  })

  it('updates pending alert to accepted and triggers unlock', async () => {
    const alertDoc = {
      _id: new mongoose.Types.ObjectId(),
      personId: new mongoose.Types.ObjectId(),
      personName: 'Visitor',
      videoUrl: '/uploads/video.mp4',
      message: 'Please open',
      status: 'pending',
      timestamp: new Date(),
      decisionTimestamp: undefined as Date | undefined,
      save: vi.fn().mockResolvedValue(undefined),
    }

    mocks.alertFindOneMock.mockResolvedValue(alertDoc)
    mocks.unlockMock.mockResolvedValue(undefined)

    mockReq.params = { id: 'alert-id' }
    mockReq.body = { status: 'accepted' }

    await updateAlertStatus(mockReq as AuthRequest, mockRes as Response, mockNext)

    expect(alertDoc.save).toHaveBeenCalledTimes(1)
    expect(mocks.unlockMock).toHaveBeenCalledTimes(1)
    expect(mockRes.json).toHaveBeenCalledWith(
      expect.objectContaining({
        alert: expect.objectContaining({
          status: 'accepted',
        }),
      })
    )
  })
})
