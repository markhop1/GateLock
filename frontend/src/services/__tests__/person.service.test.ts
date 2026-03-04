import { describe, it, expect, beforeEach, vi } from 'vitest'
import { personService } from '../person.service'
import api from '../api'

vi.mock('../api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

describe('personService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getAll', () => {
    it('should fetch all persons', async () => {
      const mockPersons = [
        { id: '1', name: 'Juan', createdAt: '2025-01-01' },
        { id: '2', name: 'María', createdAt: '2025-01-02' },
      ]
      vi.mocked(api.get).mockResolvedValue({ data: { persons: mockPersons } })

      const result = await personService.getAll()

      expect(api.get).toHaveBeenCalledWith('/persons')
      expect(result).toEqual(mockPersons)
    })
  })

  describe('getById', () => {
    it('should fetch a person by id', async () => {
      const mockPerson = { id: '1', name: 'Juan', email: 'juan@test.com', createdAt: '2025-01-01' }
      vi.mocked(api.get).mockResolvedValue({ data: { person: mockPerson } })

      const result = await personService.getById('1')

      expect(api.get).toHaveBeenCalledWith('/persons/1')
      expect(result).toEqual(mockPerson)
    })
  })

  describe('create', () => {
    it('should create a person', async () => {
      const data = { name: 'Nuevo' }
      const mockPerson = { id: '3', name: 'Nuevo', createdAt: '2025-01-03' }
      vi.mocked(api.post).mockResolvedValue({ data: { person: mockPerson } })

      const result = await personService.create(data)

      expect(api.post).toHaveBeenCalledWith('/persons', data)
      expect(result).toEqual(mockPerson)
    })

    it('should create a person with optional fields', async () => {
      const data = { name: 'Nuevo', email: 'nuevo@test.com', photoUrl: 'https://photo.jpg' }
      vi.mocked(api.post).mockResolvedValue({ data: { person: { id: '4', ...data } } })

      await personService.create(data)

      expect(api.post).toHaveBeenCalledWith('/persons', data)
    })
  })

  describe('update', () => {
    it('should update a person', async () => {
      const data = { name: 'Juan Actualizado' }
      const mockPerson = { id: '1', name: 'Juan Actualizado', createdAt: '2025-01-01' }
      vi.mocked(api.put).mockResolvedValue({ data: { person: mockPerson } })

      const result = await personService.update('1', data)

      expect(api.put).toHaveBeenCalledWith('/persons/1', data)
      expect(result).toEqual(mockPerson)
    })
  })

  describe('delete', () => {
    it('should delete a person', async () => {
      vi.mocked(api.delete).mockResolvedValue({ data: undefined })

      await personService.delete('1')

      expect(api.delete).toHaveBeenCalledWith('/persons/1')
    })
  })
})
