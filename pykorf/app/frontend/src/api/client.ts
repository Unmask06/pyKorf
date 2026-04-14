import axios, { isAxiosError } from 'axios'
import type { AxiosError } from 'axios'

export const api = axios.create({
  baseURL: '',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Response interceptor: handle session lifecycle nuances
api.interceptors.response.use(
  (response) => {
    // If backend auto-reloaded due to stale KDF, signal it
    if (response.headers['x-model-stale'] === 'true') {
      console.info('[pyKorf] Model was stale — auto-reloaded from disk')
      window.dispatchEvent(new CustomEvent('model-reloaded'))
    }
    return response
  },
  (error: AxiosError) => {
    if (error.response?.status === 409) {
      // No model loaded — router guard will redirect to /
      // The detail message tells the user why
      const detail = getErrorMessage(error, 'No model loaded')
      console.warn('[pyKorf] 409:', detail)
    }
    return Promise.reject(error)
  },
)

export function getErrorMessage(error: unknown, fallback: string): string {
  if (isAxiosError<{ detail?: string; error?: string; message?: string }>(error)) {
    return error.response?.data?.detail || error.response?.data?.error || error.response?.data?.message || error.message || fallback
  }
  if (error instanceof Error) {
    return error.message || fallback
  }
  return fallback
}
