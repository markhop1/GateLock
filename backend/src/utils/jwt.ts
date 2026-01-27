import jwt from 'jsonwebtoken'

export const generateToken = (userId: string): string => {
  const jwtSecret = process.env.JWT_SECRET
  const jwtExpiresIn = process.env.JWT_EXPIRES_IN || '7d'

  if (!jwtSecret) {
    throw new Error('JWT_SECRET is not defined')
  }

  return jwt.sign({ userId }, jwtSecret, {
    expiresIn: jwtExpiresIn,
  })
}
