import { create } from 'zustand'
import { personService, Person as PersonData, CreatePersonData } from '../services/person.service'
import { getErrorMessage } from '../types/error'

export interface Person {
  id: string
  name: string
  email?: string
  photoUrl?: string
  createdAt: Date
}

// Helper to convert PersonData to Person
const personDataToPerson = (personData: PersonData): Person => ({
  ...personData,
  createdAt: new Date(personData.createdAt),
})

interface PersonState {
  persons: Person[]
  loading: boolean
  error: string | null
  addPerson: (person: CreatePersonData) => Promise<void>
  updatePerson: (id: string, person: Partial<CreatePersonData>) => Promise<void>
  deletePerson: (id: string) => Promise<void>
  getPersonById: (id: string) => Person | undefined
  getAllPersons: () => Person[]
  fetchPersons: () => Promise<void>
}

export const usePersonStore = create<PersonState>((set, get) => ({
  persons: [],
  loading: false,
  error: null,
  addPerson: async (person) => {
    try {
      set({ loading: true, error: null })
      const personData = await personService.create(person)
      const newPerson = personDataToPerson(personData)
      set((state) => ({
        persons: [...state.persons, newPerson],
        loading: false,
      }))
    } catch (error: unknown) {
      set({
        error: getErrorMessage(error) || 'Error adding person',
        loading: false,
      })
      throw error
    }
  },
  getPersonById: (id) => {
    return get().persons.find((person) => person.id === id)
  },
  getAllPersons: () => {
    return get().persons
  },
  fetchPersons: async () => {
    try {
      set({ loading: true, error: null })
      const personsData = await personService.getAll()
      const persons = personsData.map(personDataToPerson)
      set({ persons, loading: false })
    } catch (error: unknown) {
      set({
        error: getErrorMessage(error) || 'Error fetching persons',
        loading: false,
      })
    }
  },
  updatePerson: async (id: string, person: Partial<CreatePersonData>) => {
    try {
      set({ loading: true, error: null })
      const personData = await personService.update(id, person)
      const updatedPerson = personDataToPerson(personData)
      set((state) => ({
        persons: state.persons.map((p) => (p.id === id ? updatedPerson : p)),
        loading: false,
      }))
    } catch (error: unknown) {
      set({
        error: getErrorMessage(error) || 'Error updating person',
        loading: false,
      })
      throw error
    }
  },
  deletePerson: async (id: string) => {
    try {
      set({ loading: true, error: null })
      await personService.delete(id)
      set((state) => ({
        persons: state.persons.filter((p) => p.id !== id),
        loading: false,
      }))
    } catch (error: unknown) {
      set({
        error: getErrorMessage(error) || 'Error deleting person',
        loading: false,
      })
      throw error
    }
  },
}))
