import { AxiosError } from 'axios'

export interface ApiErrorResponse {
  error: string
}

export type ApiError = AxiosError<ApiErrorResponse>

export const getErrorMessage = (error: unknown): string => {
  if (error && typeof error === 'object' && 'response' in error) {
    const axiosError = error as ApiError
    return axiosError.response?.data?.error || axiosError.message || 'An error occurred'
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'An unknown error occurred'
}
