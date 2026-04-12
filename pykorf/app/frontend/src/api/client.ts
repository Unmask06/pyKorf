import axios from 'axios'
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
      // The store will pick this up on next fetchStatus()
      console.info('[pyKorf] Model was stale — auto-reloaded from disk')
    }
    return response
  },
  (error: AxiosError) => {
    if (error.response?.status === 409) {
      // No model loaded — router guard will redirect to /
      // The detail message tells the user why
      const detail = (error.response.data as any)?.detail || 'No model loaded'
      console.warn('[pyKorf] 409:', detail)
    }
    return Promise.reject(error)
  },
)
