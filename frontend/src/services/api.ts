import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'
// Origen del backend para URLs estáticas (videos, etc.). La API está en /api, los uploads en /uploads.
const API_ORIGIN = API_URL.replace(/\/api\/?$/, '')

/**
 * Convierte una URL relativa del backend (ej: /uploads/videos/xxx.mp4) a URL absoluta.
 * Necesario porque el frontend puede estar en otro puerto/origen.
 */
export function getBackendAssetUrl(relativePath: string): string {
  if (!relativePath) return ''
  if (relativePath.startsWith('http://') || relativePath.startsWith('https://')) {
    return relativePath
  }
  const path = relativePath.startsWith('/') ? relativePath : `/${relativePath}`
  return `${API_ORIGIN}${path}`
}

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth-storage')
  if (token) {
    try {
      const authData = JSON.parse(token)
      if (authData.state?.token) {
        config.headers.Authorization = `Bearer ${authData.state.token}`
      }
    } catch {
      // Ignore parsing errors
    }
  }
  return config
})

// Handle 401 errors (unauthorized)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const reqUrl = error.config?.url ?? ''
      // Skip redirect for login/register - let the page show the error message
      if (!reqUrl.includes('/auth/login') && !reqUrl.includes('/auth/register')) {
        localStorage.removeItem('auth-storage')
          globalThis.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api
