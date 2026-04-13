import { ref } from 'vue'

export function useLoading<TArgs extends unknown[], TResult>(
  fn: (...args: TArgs) => Promise<TResult>,
) {
  const isLoading = ref(false)

  async function execute(...args: TArgs): Promise<TResult | undefined> {
    isLoading.value = true
    try {
      return await fn(...args)
    } finally {
      isLoading.value = false
    }
  }

  return { isLoading, execute }
}
