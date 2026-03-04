import { describe, it, expect, beforeEach, vi } from 'vitest'
import { alertService } from '../alert.service'
import api from '../api'

vi.mock('../api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
  },
}))

describe('alertService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getAll', () => {
    it('should fetch all alerts without status filter', async () => {
      const mockAlerts = [
        {
          id: '1',
          personId: 'p1',
          personName: 'Juan',
          videoUrl: '/videos/1.mp4',
          message: 'Test',
          status: 'pending',
          timestamp: '2025-01-01T12:00:00Z',
        },
      ]
      vi.mocked(api.get).mockResolvedValue({ data: { alerts: mockAlerts } })

      const result = await alertService.getAll()

      expect(api.get).toHaveBeenCalledWith('/alerts', { params: {} })
      expect(result).toEqual(mockAlerts)
    })

    it('should fetch alerts with status filter', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: { alerts: [] } })

      await alertService.getAll('accepted')

      expect(api.get).toHaveBeenCalledWith('/alerts', { params: { status: 'accepted' } })
    })
  })

  describe('getById', () => {
    it('should fetch a single alert by id', async () => {
      const mockAlert = {
        id: '1',
        personId: 'p1',
        personName: 'Juan',
        videoUrl: '/videos/1.mp4',
        message: 'Test',
        status: 'accepted',
        timestamp: '2025-01-01T12:00:00Z',
      }
      vi.mocked(api.get).mockResolvedValue({ data: { alert: mockAlert } })

      const result = await alertService.getById('1')

      expect(api.get).toHaveBeenCalledWith('/alerts/1')
      expect(result).toEqual(mockAlert)
    })
  })

  describe('create', () => {
    it('should create an alert', async () => {
      const data = {
        personId: 'p1',
        personName: 'Juan',
        videoUrl: '/videos/1.mp4',
        message: 'Quiere acceder',
      }
      const mockAlert = { ...data, id: '1', status: 'pending', timestamp: '2025-01-01T12:00:00Z' }
      vi.mocked(api.post).mockResolvedValue({ data: { alert: mockAlert } })

      const result = await alertService.create(data)

      expect(api.post).toHaveBeenCalledWith('/alerts', data)
      expect(result).toEqual(mockAlert)
    })
  })

  describe('updateStatus', () => {
    it('should update alert status to accepted', async () => {
      const mockAlert = {
        id: '1',
        personId: 'p1',
        personName: 'Juan',
        videoUrl: '/videos/1.mp4',
        message: 'Test',
        status: 'accepted',
        timestamp: '2025-01-01T12:00:00Z',
        decisionTimestamp: '2025-01-01T12:05:00Z',
      }
      vi.mocked(api.patch).mockResolvedValue({ data: { alert: mockAlert } })

      const result = await alertService.updateStatus('1', 'accepted')

      expect(api.patch).toHaveBeenCalledWith('/alerts/1/status', { status: 'accepted' })
      expect(result).toEqual(mockAlert)
    })

    it('should update alert status to ignored', async () => {
      vi.mocked(api.patch).mockResolvedValue({ data: { alert: {} } })

      await alertService.updateStatus('alert-2', 'ignored')

      expect(api.patch).toHaveBeenCalledWith('/alerts/alert-2/status', { status: 'ignored' })
    })
  })
})
