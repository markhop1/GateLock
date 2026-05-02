import { describe, it, expect, beforeEach, vi } from 'vitest'
import { nukiService } from '../nuki.service'
import api from '../api'

vi.mock('../api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

describe('nukiService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('gets lock status', async () => {
    const mockStatus = { configured: true, status: 'locked' as const, name: 'Front Door' }
    vi.mocked(api.get).mockResolvedValue({ data: mockStatus })

    const result = await nukiService.getStatus()

    expect(api.get).toHaveBeenCalledWith('/nuki/status')
    expect(result).toEqual(mockStatus)
  })

  it('sends unlock action', async () => {
    vi.mocked(api.post).mockResolvedValue({ data: {} })

    await nukiService.unlock()

    expect(api.post).toHaveBeenCalledWith('/nuki/action', { action: 'unlock' })
  })

  it('sends lock action', async () => {
    vi.mocked(api.post).mockResolvedValue({ data: {} })

    await nukiService.lock()

    expect(api.post).toHaveBeenCalledWith('/nuki/action', { action: 'lock' })
  })
})
