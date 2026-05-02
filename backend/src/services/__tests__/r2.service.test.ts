import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'

const { sendMock, s3ClientCtorMock } = vi.hoisted(() => ({
  sendMock: vi.fn(),
  s3ClientCtorMock: vi.fn(),
}))

vi.mock('@aws-sdk/client-s3', () => {
  class PutObjectCommand {
    input: unknown

    constructor(input: unknown) {
      this.input = input
    }
  }

  class DeleteObjectCommand {
    input: unknown

    constructor(input: unknown) {
      this.input = input
    }
  }

  return {
    S3Client: s3ClientCtorMock.mockImplementation(() => ({
      send: sendMock,
    })),
    PutObjectCommand,
    DeleteObjectCommand,
  }
})

const ORIGINAL_ENV = { ...process.env }

async function loadService() {
  return import('../r2.service.js')
}

function setR2Env() {
  process.env.R2_ACCOUNT_ID = 'acc123'
  process.env.R2_ACCESS_KEY_ID = 'key'
  process.env.R2_SECRET_ACCESS_KEY = 'secret'
  process.env.R2_BUCKET_NAME = 'videos'
  process.env.R2_PUBLIC_URL = 'https://cdn.example.com/'
}

describe('r2.service', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.clearAllMocks()
    process.env = { ...ORIGINAL_ENV }
  })

  afterEach(() => {
    process.env = { ...ORIGINAL_ENV }
  })

  it('detects configured and non-configured states', async () => {
    const serviceWithoutEnv = await loadService()
    expect(serviceWithoutEnv.isR2Configured()).toBe(false)

    vi.resetModules()
    setR2Env()
    const serviceWithEnv = await loadService()
    expect(serviceWithEnv.isR2Configured()).toBe(true)
  })

  it('uploads to r2 and returns public url', async () => {
    setR2Env()
    const service = await loadService()
    sendMock.mockResolvedValue({})

    const url = await service.uploadToR2('videos/test.mp4', Buffer.from('abc'), 'video/mp4')

    expect(s3ClientCtorMock).toHaveBeenCalledTimes(1)
    expect(sendMock).toHaveBeenCalledTimes(1)
    expect(url).toBe('https://cdn.example.com/videos/test.mp4')
  })

  it('deletes object from r2', async () => {
    setR2Env()
    const service = await loadService()
    sendMock.mockResolvedValue({})

    await service.deleteFromR2('videos/test.mp4')

    expect(s3ClientCtorMock).toHaveBeenCalledTimes(1)
    expect(sendMock).toHaveBeenCalledTimes(1)
  })

  it('throws when upload is attempted without configuration', async () => {
    const service = await loadService()

    await expect(service.uploadToR2('x', Buffer.from('a'), 'text/plain')).rejects.toThrow(
      'R2 is not configured'
    )
  })
})
