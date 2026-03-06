import api from './api'

export type LockStatus = 'locked' | 'unlocked' | 'unlatched' | 'unavailable' | 'unknown'

export type LockStatusResponse =
  | { configured: false; notConfigured: true }
  | {
      configured: true
      status: LockStatus
      name?: string
      batteryCritical?: boolean
      error?: true
    }

export const nukiService = {
  async getStatus(): Promise<LockStatusResponse> {
    const response = await api.get<LockStatusResponse>('/nuki/status')
    return response.data
  },

  async unlock(): Promise<void> {
    await api.post('/nuki/action', { action: 'unlock' })
  },

  async lock(): Promise<void> {
    await api.post('/nuki/action', { action: 'lock' })
  },
}
