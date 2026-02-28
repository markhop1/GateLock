import { Response, NextFunction } from 'express'
import { AuthRequest } from '../middleware/auth.middleware.js'
import path from 'path'
import fs from 'fs/promises'
import { v4 as uuidv4 } from 'uuid'

const UPLOAD_DIR = path.join(process.cwd(), 'uploads', 'videos')
const MAX_FILE_SIZE = 100 * 1024 * 1024 // 100 MB

// Asegurar que el directorio de uploads existe
fs.mkdir(UPLOAD_DIR, { recursive: true }).catch(() => {
  // Ignorar errores si ya existe
})

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
      // Eliminar archivo subido
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

    // Generar nombre único
    const fileExt = path.extname(req.file.originalname)
    const uniqueFilename = `${uuidv4()}${fileExt}`
    const finalPath = path.join(UPLOAD_DIR, uniqueFilename)

    // Mover archivo al directorio final
    await fs.rename(req.file.path, finalPath)

    // Generar URL del video
    const videoUrl = `/uploads/videos/${uniqueFilename}`

    res.status(201).json({
      videoUrl,
      filename: uniqueFilename,
      size: req.file.size,
    })
  } catch (error) {
    next(error)
  }
}
