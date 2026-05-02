import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'

const { nukiCtorMock, setActionMock, getSmartlockMock } = vi.hoisted(() => ({
  nukiCtorMock: vi.fn(),
  setActionMock: vi.fn(),
  getSmartlockMock: vi.fn(),
}))

vi.mock('nuki-web-api', () => ({
  default: nukiCtorMock.mockImplementation(() => ({
    setAction: setActionMock,
    getSmartlock: getSmartlockMock,
  })),
}))

const ORIGINAL_ENV = { ...process.env }

async function loadService() {
  return import('../nuki.service.js')
}

describe('nuki.service', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.clearAllMocks()
    process.env = { ...ORIGINAL_ENV }
  })

  afterEach(() => {
    process.env = { ...ORIGINAL_ENV }
  })

  it('returns not configured state when env vars are missing', async () => {
    delete process.env.NUKI_TOKEN
    delete process.env.NUKI_SMARTLOCK_ID

    const service = await loadService()

    await expect(service.unlock()).resolves.toBeUndefined()
    await expect(service.lock()).resolves.toBeUndefined()
    await expect(service.getState()).resolves.toEqual({ configured: false, notConfigured: true })
    expect(nukiCtorMock).not.toHaveBeenCalled()
  })

  it('throws when unlock is called with throwOnError and invalid smartlock id', async () => {
    process.env.NUKI_TOKEN = 'token'
    process.env.NUKI_SMARTLOCK_ID = 'abc'

    const service = await loadService()

    await expect(service.unlock({ throwOnError: true })).rejects.toThrow('Invalid NUKI_SMARTLOCK_ID')
  })

  it('throws when unlock has throwOnError and nuki action fails', async () => {
    process.env.NUKI_TOKEN = 'token'
    process.env.NUKI_SMARTLOCK_ID = '123'

    const service = await loadService()
    setActionMock.mockRejectedValue(new Error('nuki action failed'))

    await expect(service.unlock({ throwOnError: true })).rejects.toThrow('nuki action failed')
  })

  it('executes unlock and lock actions when configured', async () => {
    process.env.NUKI_TOKEN = 'token'
    process.env.NUKI_SMARTLOCK_ID = '123'

    const service = await loadService()
    setActionMock.mockResolvedValue(undefined)

    await service.unlock()
    await service.lock()

    expect(nukiCtorMock).toHaveBeenCalledWith('token')
    expect(setActionMock).toHaveBeenCalledWith(123, 1)
    expect(setActionMock).toHaveBeenCalledWith(123, 2)
  })

  it('executes unlatch action when NUKI_ACTION is unlatch', async () => {
    process.env.NUKI_TOKEN = 'token'
    process.env.NUKI_SMARTLOCK_ID = '123'
    process.env.NUKI_ACTION = 'unlatch'

    const service = await loadService()
    setActionMock.mockResolvedValue(undefined)

    await service.unlock()

    expect(setActionMock).toHaveBeenCalledWith(123, 3)
  })

  it('returns unavailable state when smartlock id is invalid in getState', async () => {
    process.env.NUKI_TOKEN = 'token'
    process.env.NUKI_SMARTLOCK_ID = 'abc'

    const service = await loadService()

    await expect(service.getState()).resolves.toEqual({ configured: true, status: 'unavailable', error: true })
  })

  it('returns unavailable when nuki state is 0', async () => {
    process.env.NUKI_TOKEN = 'token'
    process.env.NUKI_SMARTLOCK_ID = '123'

    const service = await loadService()
    getSmartlockMock.mockResolvedValueOnce({ state: 0 })

    await expect(service.getState()).resolves.toMatchObject({ configured: true, status: 'unavailable' })
  })

  it('maps lock states from numeric and nested state object', async () => {
    process.env.NUKI_TOKEN = 'token'
    process.env.NUKI_SMARTLOCK_ID = '123'

    const service = await loadService()

    getSmartlockMock.mockResolvedValueOnce({ state: { state: 1 }, name: 'Door', batteryCritical: false })
    await expect(service.getState()).resolves.toMatchObject({ configured: true, status: 'locked', name: 'Door' })

    getSmartlockMock.mockResolvedValueOnce({ state: 3 })
    await expect(service.getState()).resolves.toMatchObject({ configured: true, status: 'unlatched' })

    getSmartlockMock.mockResolvedValueOnce({ state: 4 })
    await expect(service.getState()).resolves.toMatchObject({ configured: true, status: 'unlocked' })
  })

  it('maps unknown state when it cannot infer a numeric state', async () => {
    process.env.NUKI_TOKEN = 'token'
    process.env.NUKI_SMARTLOCK_ID = '123'

    const service = await loadService()
    getSmartlockMock.mockResolvedValueOnce({ state: null, config: {} })

    await expect(service.getState()).resolves.toMatchObject({ configured: true, status: 'unknown' })
  })

  it('returns unavailable on nuki api error', async () => {
    process.env.NUKI_TOKEN = 'token'
    process.env.NUKI_SMARTLOCK_ID = '123'

    const service = await loadService()
    getSmartlockMock.mockRejectedValue(new Error('boom'))

    await expect(service.getState()).resolves.toEqual({ configured: true, status: 'unavailable', error: true })
  })
})
