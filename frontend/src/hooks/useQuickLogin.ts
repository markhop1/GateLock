import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

/**
 * Hook to enable quick login with Ctrl+Shift+K shortcut
 * Uses test credentials for development/testing purposes
 * If the test user doesn't exist, it will try to create it automatically
 */
export function useQuickLogin() {
  const navigate = useNavigate()

  useEffect(() => {
    const handleKeyDown = async (event: KeyboardEvent) => {
      // Check for Ctrl+Shift+K (or Cmd+Shift+K on Mac)
      if (
        (event.ctrlKey || event.metaKey) &&
        event.shiftKey &&
        event.key === 'K'
      ) {
        event.preventDefault()
        
        const { login, register, isAuthenticated } = useAuthStore.getState()
        
        // If already authenticated, do nothing
        if (isAuthenticated) {
          console.log('Already logged in!')
          return
        }
        
        const testEmail = 'test@example.com'
        const testPassword = 'test123'
        const testName = 'Test User'
        
        try {
          // Try to login first
          await login(testEmail, testPassword)
          navigate('/')
          console.log('Quick login successful!')
        } catch (error) {
          console.log('Test user not found, attempting to create...')
          // Try to create the test user if it doesn't exist
          try {
            await register(testEmail, testPassword, testName)
            await login(testEmail, testPassword)
            navigate('/')
            console.log('Test user created and logged in!')
          } catch (registerError: any) {
            console.error('Failed to create test user:', registerError)
            const errorMsg = registerError?.response?.data?.error || registerError?.message || 'Unknown error'
            alert(`Quick login failed: ${errorMsg}\n\nPlease register manually or check the console.`)
          }
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [navigate])
}
