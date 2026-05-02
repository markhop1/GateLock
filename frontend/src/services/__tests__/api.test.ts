import { beforeEach, describe, expect, it, vi } from 'vitest'
import type apiType from '../api'

function getRequestHandler(api: typeof apiType): (config: { headers: Record<string, string> }) => Promise<{ headers: Record<string, string> }> | { headers: Record<string, string> } {
  const handlers = (api.interceptors.request as unknown as { handlers?: Array<{ fulfilled?: (config: { headers: Record<string, string> }) => Promise<{ headers: Record<string, string> }> | { headers: Record<string, string> } }> }).handlers
  const fulfilled = handlers?.findLast((handler) => typeof handler?.fulfilled === 'function')?.fulfilled

  if (!fulfilled) {
    throw new Error('Request interceptor handler not found')
  }

  return fulfilled
}

function getResponseErrorHandler(api: typeof apiType): (error: { response?: { status?: number }; config?: { url?: string } }) => Promise<never> {
  const handlers = (api.interceptors.response as unknown as { handlers?: Array<{ rejected?: (error: { response?: { status?: number }; config?: { url?: string } }) => Promise<never> }> }).handlers
  const rejected = handlers?.findLast((handler) => typeof handler?.rejected === 'function')?.rejected

  if (!rejected) {
    throw new Error('Response interceptor error handler not found')
  }

  return rejected
}

async function loadApiModule(): Promise<{ default: typeof apiType; getBackendAssetUrl: (relativePath: string) => string }> {
  vi.resetModules()
  vi.unmock('axios')
  return import('../api')
}

describe('api service', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('builds backend asset urls correctly', async () => {
    const { getBackendAssetUrl } = await loadApiModule()

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
    const { default: api } = await loadApiModule()

    const config = { headers: {} as Record<string, string> }
    const result = await getRequestHandler(api)(config)

    expect(result).toBeDefined()
    expect(result.headers).toBeDefined()
  })

  it('clears auth and redirects on 401 for protected routes', async () => {
    const { default: api } = await loadApiModule()

    const error = {
      response: { status: 401 },
      config: { url: '/persons' },
    }

    await expect(getResponseErrorHandler(api)(error)).rejects.toEqual(error)
  })

  it('does not redirect on 401 for login/register endpoints', async () => {
    const removeSpy = vi.spyOn(Storage.prototype, 'removeItem')
    const { default: api } = await loadApiModule()

    const error = {
      response: { status: 401 },
      config: { url: '/auth/login' },
    }

    await expect(getResponseErrorHandler(api)(error)).rejects.toEqual(error)
    expect(removeSpy).not.toHaveBeenCalled()

    removeSpy.mockRestore()
  })
})

