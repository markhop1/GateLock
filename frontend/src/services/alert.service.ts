import api from './api'

export type AlertStatus = 'pending' | 'accepted' | 'ignored' | 'unanswered'

export interface Alert {
  id: string
  personId: string
  personName: string
  videoUrl: string
  message: string
  status: AlertStatus
  timestamp: string
  decisionTimestamp?: string
}

export interface CreateAlertData {
  personId: string
  personName: string
  videoUrl: string
  message: string
}

export const alertService = {
  async getAll(status?: AlertStatus): Promise<Alert[]> {
    const params = status ? { status } : {}
    const response = await api.get<{ alerts: Alert[] }>('/alerts', { params })
    return response.data.alerts
  },

  async getById(id: string): Promise<Alert> {
    const response = await api.get<{ alert: Alert }>(`/alerts/${id}`)
    return response.data.alert
  },

  async create(data: CreateAlertData): Promise<Alert> {
    const response = await api.post<{ alert: Alert }>('/alerts', data)
    return response.data.alert
  },

  async updateStatus(id: string, status: 'accepted' | 'ignored'): Promise<Alert> {
    const response = await api.patch<{ alert: Alert }>(`/alerts/${id}/status`, {
      status,
    })
    return response.data.alert
  },
}
