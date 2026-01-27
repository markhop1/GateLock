import { describe, it, expect, beforeEach, vi } from 'vitest'
import { usePersonStore } from '../personStore'
import { personService, Person } from '../../services/person.service'

// Mock person service
vi.mock('../../services/person.service', () => ({
  personService: {
    getAll: vi.fn(),
    getById: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
}))

describe('Person Store', () => {
  beforeEach(() => {
    // Reset store state
    usePersonStore.setState({
      persons: [],
      loading: false,
      error: null,
    })
    vi.clearAllMocks()
  })

  describe('addPerson', () => {
    it('should add person to store on success', async () => {
      const mockPerson = {
        id: '1',
        name: 'Test Person',
        email: 'test@example.com',
        createdAt: '2024-01-01T00:00:00Z',
      }

      vi.mocked(personService.create).mockResolvedValue(mockPerson)

      await usePersonStore.getState().addPerson({
        name: 'Test Person',
        email: 'test@example.com',
      })

      const state = usePersonStore.getState()
      expect(state.persons).toHaveLength(1)
      expect(state.persons[0].name).toBe('Test Person')
      expect(state.loading).toBe(false)
      expect(state.error).toBeNull()
    })

    it('should set error on failure', async () => {
      const error = new Error('Failed to create person')
      vi.mocked(personService.create).mockRejectedValue(error)

      await expect(
        usePersonStore.getState().addPerson({ name: 'Test Person' })
      ).rejects.toThrow()

      const state = usePersonStore.getState()
      expect(state.error).toBeTruthy()
      expect(state.loading).toBe(false)
    })
  })

  describe('updatePerson', () => {
    it('should update person in store', async () => {
      // First add a person with Date object (as the store expects)
      const initialPerson = {
        id: '1',
        name: 'Original Name',
        createdAt: new Date('2024-01-01T00:00:00Z'),
      }
      usePersonStore.setState({
        persons: [initialPerson],
      })

      const updatedPerson = {
        id: '1',
        name: 'Updated Name',
        createdAt: '2024-01-01T00:00:00Z',
      }

      vi.mocked(personService.update).mockResolvedValue(updatedPerson)

      await usePersonStore.getState().updatePerson('1', { name: 'Updated Name' })

      const state = usePersonStore.getState()
      expect(state.persons[0].name).toBe('Updated Name')
    })
  })

  describe('deletePerson', () => {
    it('should remove person from store', async () => {
      const person = {
        id: '1',
        name: 'Test Person',
        createdAt: new Date('2024-01-01T00:00:00Z'),
      }
      usePersonStore.setState({
        persons: [person],
      })

      vi.mocked(personService.delete).mockResolvedValue(undefined)

      await usePersonStore.getState().deletePerson('1')

      const state = usePersonStore.getState()
      expect(state.persons).toHaveLength(0)
    })
  })

  describe('fetchPersons', () => {
    it('should fetch and set persons', async () => {
      const mockPersons = [
        {
          id: '1',
          name: 'Person 1',
          createdAt: '2024-01-01T00:00:00Z',
        },
        {
          id: '2',
          name: 'Person 2',
          createdAt: '2024-01-02T00:00:00Z',
        },
      ]

      vi.mocked(personService.getAll).mockResolvedValue(mockPersons as Person[])

      await usePersonStore.getState().fetchPersons()

      const state = usePersonStore.getState()
      expect(state.persons).toHaveLength(2)
      expect(state.loading).toBe(false)
    })
  })
})
