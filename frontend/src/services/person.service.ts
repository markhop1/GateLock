import api from './api'

export interface Person {
  id: string
  name: string
  email?: string
  photoUrl?: string
  createdAt: string
}

export interface CreatePersonData {
  name: string
  email?: string
  photoUrl?: string
}

export const personService = {
  async getAll(): Promise<Person[]> {
    const response = await api.get<{ persons: Person[] }>('/persons')
    return response.data.persons
  },

  async getById(id: string): Promise<Person> {
    const response = await api.get<{ person: Person }>(`/persons/${id}`)
    return response.data.person
  },

  async create(data: CreatePersonData): Promise<Person> {
    const response = await api.post<{ person: Person }>('/persons', data)
    return response.data.person
  },

  async update(id: string, data: Partial<CreatePersonData>): Promise<Person> {
    const response = await api.put<{ person: Person }>(`/persons/${id}`, data)
    return response.data.person
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/persons/${id}`)
  },
}
