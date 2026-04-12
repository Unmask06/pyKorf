import { ref } from 'vue'

export function useLoading<T extends (...args: any[]) => Promise<any>>(
  fn: T,
) {
  const isLoading = ref(false)

  async function execute(...args: Parameters<T>): Promise<ReturnType<T> | undefined> {
    isLoading.value = true
    try {
      return await fn(...args)
    } finally {
      isLoading.value = false
    }
  }

  return { isLoading, execute }
}
