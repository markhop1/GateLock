import { describe, it, expect, beforeEach, vi } from 'vitest'
import { Response } from 'express'
import { uploadVideo } from '../video.controller.js'
import { AuthRequest } from '../../middleware/auth.middleware.js'

const { mockUnlink, mockRename } = vi.hoisted(() => ({
  mockUnlink: vi.fn().mockResolvedValue(undefined),
  mockRename: vi.fn().mockResolvedValue(undefined),
}))

vi.mock('fs/promises', async (importOriginal) => {
  const actual = await importOriginal<typeof import('fs/promises')>()
  return {
    ...actual,
    default: {
      ...actual.default,
      mkdir: vi.fn().mockResolvedValue(undefined),
      unlink: mockUnlink,
      rename: mockRename,
    },
    unlink: mockUnlink,
    rename: mockRename,
  }
})

vi.mock('path', () => ({
  default: {
    join: (...args: string[]) => args.join('/'),
    extname: (p: string) => {
      const match = p.match(/\.\w+$/)
      return match ? match[0] : ''
    },
  },
}))

vi.mock('uuid', () => ({
  v4: vi.fn(() => 'unique-uuid-123'),
}))

describe('Video Controller', () => {
  let mockReq: Partial<AuthRequest>
  let mockRes: Partial<Response>
  let mockNext: ReturnType<typeof vi.fn>

  beforeEach(() => {
    mockReq = {
      body: {},
      userId: 'user-id-123',
    }
    mockRes = {
      status: vi.fn().mockReturnThis(),
      json: vi.fn().mockReturnThis(),
    }
    mockNext = vi.fn()
    vi.clearAllMocks()
  })

  it('should return 400 if no file is provided', async () => {
    mockReq.file = undefined

    await uploadVideo(mockReq as AuthRequest, mockRes as Response, mockNext)

    expect(mockRes.status).toHaveBeenCalledWith(400)
    expect(mockRes.json).toHaveBeenCalledWith({
      error: 'No se proporcionó archivo de video',
    })
    expect(mockNext).not.toHaveBeenCalled()
  })

  it('should return 400 for invalid file type', async () => {
    mockReq.file = {
      fieldname: 'video',
      originalname: 'test.pdf',
      mimetype: 'application/pdf',
      path: '/tmp/test.pdf',
      size: 1024,
      stream: null as never,
      destination: '',
      filename: '',
      buffer: null as never,
    }

    await uploadVideo(mockReq as AuthRequest, mockRes as Response, mockNext)

    expect(mockUnlink).toHaveBeenCalledWith('/tmp/test.pdf')
    expect(mockRes.status).toHaveBeenCalledWith(400)
    expect(mockRes.json).toHaveBeenCalledWith({
      error: 'Tipo de archivo no permitido. Solo se permiten videos MP4, MOV, AVI',
    })
    expect(mockNext).not.toHaveBeenCalled()
  })

  it('should return 400 for file exceeding size limit', async () => {
    const maxSize = 100 * 1024 * 1024 + 1
    mockReq.file = {
      fieldname: 'video',
      originalname: 'large.mp4',
      mimetype: 'video/mp4',
      path: '/tmp/large.mp4',
      size: maxSize,
      stream: null as never,
      destination: '',
      filename: '',
      buffer: null as never,
    }

    await uploadVideo(mockReq as AuthRequest, mockRes as Response, mockNext)

    expect(mockUnlink).toHaveBeenCalledWith('/tmp/large.mp4')
    expect(mockRes.status).toHaveBeenCalledWith(400)
    expect(mockRes.json).toHaveBeenCalledWith({
      error: 'Archivo demasiado grande. Tamaño máximo: 100MB',
    })
    expect(mockNext).not.toHaveBeenCalled()
  })

  it('should return 201 with videoUrl on successful upload', async () => {
    mockReq.file = {
      fieldname: 'video',
      originalname: 'test.mp4',
      mimetype: 'video/mp4',
      path: '/tmp/temp-123',
      size: 1024 * 1024,
      stream: null as never,
      destination: '',
      filename: '',
      buffer: null as never,
    }

    await uploadVideo(mockReq as AuthRequest, mockRes as Response, mockNext)

    expect(mockRename).toHaveBeenCalled()
    expect(mockRes.status).toHaveBeenCalledWith(201)
    expect(mockRes.json).toHaveBeenCalledWith({
      videoUrl: '/uploads/videos/unique-uuid-123.mp4',
      filename: 'unique-uuid-123.mp4',
      size: 1024 * 1024,
    })
    expect(mockNext).not.toHaveBeenCalled()
  })
})
