# GateLock Backend

Backend API para el sistema de control de acceso GateLock construido con Node.js, Express, TypeScript y MongoDB.

## Características

- Express 5 con TypeScript
- MongoDB con Mongoose
- Autenticación JWT
- Validación de datos
- Manejo de errores centralizado
- CORS configurado
- Tests con Vitest

## Requisitos

- Node.js >= 20.0.0
- npm >= 10.0.0
- MongoDB (local o MongoDB Atlas)

## Instalación

```bash
cd backend
npm install
```

## Configuración

1. Copia el archivo `.env.example` a `.env`:
```bash
cp .env.example .env
```

2. Edita `.env` con tus credenciales:
```env
PORT=5000
NODE_ENV=development
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/gatelock
JWT_SECRET=your-super-secret-jwt-key
JWT_EXPIRES_IN=7d
CORS_ORIGIN=http://localhost:3000
```

## Ejecutar

### Desarrollo
```bash
npm run dev
```

### Producción
```bash
npm run build
npm start
```

## Endpoints

### Autenticación
- `POST /api/auth/register` - Registro de usuario
- `POST /api/auth/login` - Inicio de sesión
- `GET /api/auth/me` - Obtener usuario actual (requiere autenticación)

### Personas
- `POST /api/persons` - Crear persona
- `GET /api/persons` - Listar todas las personas
- `GET /api/persons/:id` - Obtener persona por ID
- `PUT /api/persons/:id` - Actualizar persona
- `DELETE /api/persons/:id` - Eliminar persona

### Alertas
- `POST /api/alerts` - Crear alerta
- `GET /api/alerts` - Listar alertas
- `GET /api/alerts/:id` - Obtener alerta por ID
- `PATCH /api/alerts/:id/status` - Actualizar estado de alerta

### Videos
- `POST /api/videos/upload` - Subir video (multipart, requiere autenticación)

### Nuki Smart Lock
- `GET /api/nuki/status` - Estado del cerrojo
- `POST /api/nuki/unlock` - Desbloquear
- `POST /api/nuki/lock` - Bloquear

### Health Check
- `GET /api/health` - Estado del servidor

## Autenticación

Todas las rutas excepto `/api/auth/*` y `/api/health` requieren autenticación.

Incluye el token JWT en el header:
```
Authorization: Bearer <token>
```

## Estructura del proyecto

```
backend/
├── src/
│   ├── config/          # Configuración (database, etc.)
│   ├── controllers/     # Controladores de rutas
│   ├── middleware/      # Middleware (auth, error handling)
│   ├── models/          # Modelos de Mongoose
│   ├── routes/          # Definición de rutas
│   ├── services/        # Nuki, etc.
│   ├── utils/           # Utilidades (JWT, etc.)
│   └── index.ts         # Punto de entrada
├── dist/                # Build de producción
└── package.json
```


## Scripts disponibles

- `npm run dev` - Inicia servidor en modo desarrollo con hot reload
- `npm run build` - Compila TypeScript a JavaScript
- `npm start` - Inicia servidor de producción
- `npm run test` - Ejecuta tests
- `npm run test:coverage` - Ejecuta tests con cobertura
- `npm run lint` - Ejecuta el linter
- `npm run type-check` - Verifica tipos sin compilar
