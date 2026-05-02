import { Response, NextFunction } from 'express'
import { AuthRequest } from '../middleware/auth.middleware.js'
import path from 'node:path'
import fs from 'node:fs/promises'
import { v4 as uuidv4 } from 'uuid'
import { isR2Configured, uploadToR2 } from '../services/r2.service.js'

const UPLOAD_DIR = path.join(process.cwd(), 'uploads', 'videos')
const MAX_FILE_SIZE = 100 * 1024 * 1024 // 100 MB

// Asegurar que el directorio de uploads existe (para modo local)
await fs.mkdir(UPLOAD_DIR, { recursive: true })

export const uploadVideo = async (
  req: AuthRequest,
  res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    if (!req.file) {
      res.status(400).json({
        error: 'No se proporcionó archivo de video',
      })
      return
    }

    // Validar tipo de archivo
    const allowedMimeTypes = ['video/mp4', 'video/quicktime', 'video/x-msvideo']
    if (!allowedMimeTypes.includes(req.file.mimetype)) {
      await fs.unlink(req.file.path).catch(() => {})
      res.status(400).json({
        error: 'Tipo de archivo no permitido. Solo se permiten videos MP4, MOV, AVI',
      })
      return
    }

    // Validar tamaño
    if (req.file.size > MAX_FILE_SIZE) {
      await fs.unlink(req.file.path).catch(() => {})
      res.status(400).json({
        error: `Archivo demasiado grande. Tamaño máximo: ${MAX_FILE_SIZE / 1024 / 1024}MB`,
      })
      return
    }

    const fileExt = path.extname(req.file.originalname)
    const uniqueFilename = `${uuidv4()}${fileExt}`

    if (isR2Configured()) {
      // Upload to Cloudflare R2
      const fileBuffer = await fs.readFile(req.file.path)
      await fs.unlink(req.file.path).catch(() => {})

      const videoUrl = await uploadToR2(
        uniqueFilename,
        fileBuffer,
        req.file.mimetype
      )

      res.status(201).json({
        videoUrl,
        filename: uniqueFilename,
        size: req.file.size,
      })
    } else {
      // Local filesystem (development)
      const finalPath = path.join(UPLOAD_DIR, uniqueFilename)
      await fs.rename(req.file.path, finalPath)
      const videoUrl = `/uploads/videos/${uniqueFilename}`

      res.status(201).json({
        videoUrl,
        filename: uniqueFilename,
        size: req.file.size,
      })
    }
  } catch (error) {
    next(error)
  }
}
