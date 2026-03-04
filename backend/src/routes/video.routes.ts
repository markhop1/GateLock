import { Router } from 'express'
import multer from 'multer'
import path from 'path'
import { uploadVideo } from '../controllers/video.controller.js'
import { authenticate } from '../middleware/auth.middleware.js'

const router = Router()

// Configurar multer para almacenamiento temporal
const upload = multer({
  dest: path.join(process.cwd(), 'uploads', 'temp'),
  limits: {
    fileSize: 100 * 1024 * 1024, // 100 MB
  },
  fileFilter: (_req, file, cb) => {
    // Validar tipo de archivo
    const allowedMimeTypes = ['video/mp4', 'video/quicktime', 'video/x-msvideo']
    if (allowedMimeTypes.includes(file.mimetype)) {
      cb(null, true)
    } else {
      cb(new Error('Tipo de archivo no permitido. Solo se permiten videos MP4, MOV, AVI'))
    }
  },
})

// Todas las rutas requieren autenticación
router.use(authenticate)

// eslint-disable-next-line @typescript-eslint/no-explicit-any
router.post('/upload', upload.single('video'), uploadVideo as any)

export default router
