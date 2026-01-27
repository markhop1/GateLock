# GateLock Frontend

Frontend de la aplicación GateLock construido con React, TypeScript, Vite y Tailwind CSS.

## Características

- React 19 con TypeScript
- Vite para desarrollo rápido
- Tailwind CSS para estilos
- React Router para navegación
- Zustand para gestión de estado
- Diseño responsive (móvil y desktop)
- Soporte para modo oscuro
- Tests con Vitest

## Instalación

```bash
npm install
```

## Desarrollo

```bash
npm run dev
```

## Scripts disponibles

- `npm run dev` - Inicia el servidor de desarrollo
- `npm run build` - Construye la aplicación para producción
- `npm run preview` - Previsualiza la build de producción
- `npm run lint` - Ejecuta el linter
- `npm run test` - Ejecuta los tests
- `npm run test:ui` - Ejecuta los tests con interfaz gráfica
- `npm run test:coverage` - Ejecuta los tests con cobertura

## Estructura del proyecto

```
frontend/
├── src/
│   ├── components/     # Componentes reutilizables
│   ├── layouts/         # Layouts de la aplicación
│   ├── pages/           # Páginas principales
│   ├── store/           # Stores de Zustand
│   ├── test/            # Configuración de tests
│   └── main.tsx         # Punto de entrada
├── public/              # Archivos estáticos
└── package.json
```

## Simular notificaciones

Para probar las notificaciones, abre la consola del navegador y ejecuta:

```javascript
simulateNotification()
```

O con un nombre específico:

```javascript
simulateNotification('Nombre Persona')
```

## Tecnologías

- React 19
- TypeScript
- Vite 6
- Tailwind CSS 3
- React Router 7
- Zustand 5
- Vitest
- Heroicons
