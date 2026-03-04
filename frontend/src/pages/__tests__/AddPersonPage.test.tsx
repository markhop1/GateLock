import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import AddPersonPage from '../AddPersonPage'
import { usePersonStore } from '../../store/personStore'
import { useNotificationStore } from '../../store/notificationStore'

vi.mock('../../store/personStore', () => ({
  usePersonStore: vi.fn(),
}))

vi.mock('../../store/notificationStore', () => ({
  useNotificationStore: vi.fn(),
}))

describe('AddPersonPage', () => {
  const mockAddPerson = vi.fn()
  const mockFetchPersons = vi.fn()
  const mockFetchNotifications = vi.fn()

  beforeEach(() => {
    vi.mocked(usePersonStore).mockImplementation((selector) => {
      const state = {
        persons: [],
        loading: false,
        error: null,
        addPerson: mockAddPerson,
        updatePerson: vi.fn(),
        deletePerson: vi.fn(),
        fetchPersons: mockFetchPersons,
      }
      return selector ? selector(state) : state
    })
    vi.mocked(useNotificationStore).mockImplementation((selector) => {
      const state = {
        fetchNotifications: mockFetchNotifications,
      }
      return selector ? selector(state) : state
    })
    vi.clearAllMocks()
  })

  it('renders title and add button', () => {
    render(
      <BrowserRouter>
        <AddPersonPage />
      </BrowserRouter>
    )

    expect(screen.getByRole('heading', { name: /gestión de acceso/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /añadir persona/i })).toBeInTheDocument()
  })

  it('calls fetchPersons on mount', () => {
    render(
      <BrowserRouter>
        <AddPersonPage />
      </BrowserRouter>
    )

    expect(mockFetchPersons).toHaveBeenCalled()
  })

  it('shows add form when clicking Añadir Persona', async () => {
    const user = userEvent.setup()
    render(
      <BrowserRouter>
        <AddPersonPage />
      </BrowserRouter>
    )

    await user.click(screen.getByRole('button', { name: /añadir primera persona/i }))

    expect(screen.getByRole('heading', { name: /añadir nueva persona/i })).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/nombre de la persona/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /^añadir$/i })).toBeInTheDocument()
  })

  it('shows empty state when no persons', () => {
    render(
      <BrowserRouter>
        <AddPersonPage />
      </BrowserRouter>
    )

    expect(screen.getByText(/no hay personas registradas/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /añadir primera persona/i })).toBeInTheDocument()
  })

  it('shows validation error when submitting only spaces', async () => {
    const user = userEvent.setup()
    render(
      <BrowserRouter>
        <AddPersonPage />
      </BrowserRouter>
    )

    await user.click(screen.getByRole('button', { name: /añadir primera persona/i }))
    await user.type(screen.getByPlaceholderText(/nombre de la persona/i), '   ')
    await user.click(screen.getByRole('button', { name: /^añadir$/i }))

    await waitFor(() => {
      expect(screen.getByText(/el nombre es obligatorio/i)).toBeInTheDocument()
    })
    expect(mockAddPerson).not.toHaveBeenCalled()
  })

  it('adds person successfully and shows success message', async () => {
    const user = userEvent.setup()
    mockAddPerson.mockResolvedValue(undefined)
    vi.mocked(usePersonStore).mockImplementation((selector) => {
      const state = {
        persons: [],
        loading: false,
        error: null,
        addPerson: mockAddPerson,
        updatePerson: vi.fn(),
        deletePerson: vi.fn(),
        fetchPersons: mockFetchPersons,
      }
      return selector ? selector(state) : state
    })

    render(
      <BrowserRouter>
        <AddPersonPage />
      </BrowserRouter>
    )

    await user.click(screen.getByRole('button', { name: /añadir primera persona/i }))
    await user.type(screen.getByPlaceholderText(/nombre de la persona/i), 'Juan Pérez')
    await user.click(screen.getByRole('button', { name: /^añadir$/i }))

    await waitFor(() => {
      expect(mockAddPerson).toHaveBeenCalledWith({ name: 'Juan Pérez' })
    })
    expect(screen.getByText(/operación completada correctamente/i)).toBeInTheDocument()
  })

  it('displays existing persons list', () => {
    vi.mocked(usePersonStore).mockImplementation((selector) => {
      const state = {
        persons: [
          {
            id: '1',
            name: 'María García',
            createdAt: new Date('2025-01-01'),
          },
        ],
        loading: false,
        error: null,
        addPerson: mockAddPerson,
        updatePerson: vi.fn(),
        deletePerson: vi.fn(),
        fetchPersons: mockFetchPersons,
      }
      return selector ? selector(state) : state
    })

    render(
      <BrowserRouter>
        <AddPersonPage />
      </BrowserRouter>
    )

    expect(screen.getByText('María García')).toBeInTheDocument()
    expect(screen.getByText(/personas registradas \(1\)/i)).toBeInTheDocument()
  })
})
