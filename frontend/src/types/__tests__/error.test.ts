import { describe, it, expect } from 'vitest'
import { getErrorMessage } from '../error'

describe('getErrorMessage', () => {
  it('returns response error message for axios-like errors', () => {
    const error = {
      response: {
        data: {
          error: 'Backend says no',
        },
      },
      message: 'Request failed',
    }

    expect(getErrorMessage(error)).toBe('Backend says no')
  })

  it('falls back to axios-like message when response error is missing', () => {
    const error = {
      response: {
        data: {},
      },
      message: 'Request failed',
    }

    expect(getErrorMessage(error)).toBe('Request failed')
  })

  it('returns native error message', () => {
    expect(getErrorMessage(new Error('Native error'))).toBe('Native error')
  })

  it('returns unknown message for non-error values', () => {
    expect(getErrorMessage('oops')).toBe('An unknown error occurred')
  })
})
