import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { generateToken } from '../jwt.js'

describe('JWT Utils', () => {
  const originalEnv = process.env

  beforeEach(() => {
    process.env = { ...originalEnv }
    process.env.JWT_SECRET = 'test-secret-key'
    process.env.JWT_EXPIRES_IN = '7d'
  })

  afterEach(() => {
    process.env = originalEnv
  })

  describe('generateToken', () => {
    it('should generate a valid JWT token', () => {
      const userId = '507f1f77bcf86cd799439011'
      const token = generateToken(userId)

      expect(token).toBeDefined()
      expect(typeof token).toBe('string')
      expect(token.split('.')).toHaveLength(3) // JWT has 3 parts
    })

    it('should throw error if JWT_SECRET is not defined', () => {
      delete process.env.JWT_SECRET

      expect(() => {
        generateToken('507f1f77bcf86cd799439011')
      }).toThrow('JWT_SECRET is not defined')
    })

    it('should use default expiresIn if not provided', () => {
      delete process.env.JWT_EXPIRES_IN
      const userId = '507f1f77bcf86cd799439011'
      
      const token = generateToken(userId)
      expect(token).toBeDefined()
    })
  })
})
