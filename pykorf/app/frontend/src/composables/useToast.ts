import { reactive } from 'vue'

export interface Toast {
  type: 'success' | 'error' | 'warning' | 'info'
  message: string
}

const state = reactive<{ toasts: Toast[] }>({ toasts: [] })

export function useToastStore() {
  function add(type: Toast['type'], message: string, duration = 3000) {
    const toast: Toast = { type, message }
    state.toasts.push(toast)
    if (duration > 0) {
      setTimeout(() => {
        const idx = state.toasts.indexOf(toast)
        if (idx !== -1) state.toasts.splice(idx, 1)
      }, duration)
    }
  }

  function remove(index: number) {
    state.toasts.splice(index, 1)
  }

  function success(msg: string) { add('success', msg) }
  function error(msg: string) { add('error', msg, 5000) }
  function warning(msg: string) { add('warning', msg) }
  function info(msg: string) { add('info', msg) }

  return {
    toasts: state.toasts,
    add,
    remove,
    success,
    error,
    warning,
    info,
  }
}
