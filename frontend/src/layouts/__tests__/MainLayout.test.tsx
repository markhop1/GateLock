import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import MainLayout from '../MainLayout'

describe('MainLayout', () => {
  it('renders navigation items and child content', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <MainLayout>
          <div>Contenido principal</div>
        </MainLayout>
      </MemoryRouter>
    )

    expect(screen.getAllByText('Inicio').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Historial').length).toBeGreaterThan(0)
    expect(screen.queryByText('Acceso')).not.toBeInTheDocument()
    expect(screen.getAllByText('Candado').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Ajustes').length).toBeGreaterThan(0)
    expect(screen.getByText('Contenido principal')).toBeInTheDocument()
  })
})
