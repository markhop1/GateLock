import { beforeEach, describe, expect, it, vi } from 'vitest'

let requestHandler: ((config: any) => any) | undefined
let responseErrorHandler: ((error: any) => any) | undefined

const createMock = vi.fn(() => ({
  interceptors: {
    request: {
      use: vi.fn((handler: (config: any) => any) => {
        requestHandler = handler
      }),
    },
    response: {
      use: vi.fn((_: unknown, errorHandler: (error: any) => any) => {
        responseErrorHandler = errorHandler
      }),
    },
  },
}))

vi.mock('axios', () => ({
  default: {
    create: createMock,
  },
}))

describe('api service', () => {
  beforeEach(async () => {
    vi.resetModules()
    vi.clearAllMocks()
    requestHandler = undefined
    responseErrorHandler = undefined
    localStorage.clear()
    await import('../api')
  })

  it('builds backend asset urls correctly', async () => {
    const { getBackendAssetUrl } = await import('../api')

    expect(getBackendAssetUrl('')).toBe('')
    expect(getBackendAssetUrl('/uploads/videos/a.mp4')).toBe('http://localhost:5000/uploads/videos/a.mp4')
    expect(getBackendAssetUrl('uploads/videos/a.mp4')).toBe('http://localhost:5000/uploads/videos/a.mp4')
    expect(getBackendAssetUrl('https://cdn.example.com/a.mp4')).toBe('https://cdn.example.com/a.mp4')
  })

  it('adds auth token to request headers when present', async () => {
    localStorage.setItem(
      'auth-storage',
      JSON.stringify({ state: { token: 'jwt-token' } })
    )
    await import('../api')

    const config = { headers: {} as Record<string, string> }
    const result = await requestHandler?.(config)

    expect(result.headers.Authorization).toBe('Bearer jwt-token')
  })

  it('clears auth and redirects on 401 for protected routes', async () => {
    localStorage.setItem('auth-storage', JSON.stringify({ state: { token: 'jwt-token' } }))
    const removeSpy = vi.spyOn(Storage.prototype, 'removeItem')

    await import('../api')

    const error = {
      response: { status: 401 },
      config: { url: '/persons' },
    }

    await expect(responseErrorHandler?.(error)).rejects.toEqual(error)
    expect(removeSpy).toHaveBeenCalledWith('auth-storage')
  })

  it('does not redirect on 401 for login/register endpoints', async () => {
    const removeSpy = vi.spyOn(Storage.prototype, 'removeItem')

    await import('../api')

    const error = {
      response: { status: 401 },
      config: { url: '/auth/login' },
    }

    await expect(responseErrorHandler?.(error)).rejects.toEqual(error)
    expect(removeSpy).not.toHaveBeenCalled()
  })
})
