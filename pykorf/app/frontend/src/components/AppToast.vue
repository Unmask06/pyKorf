<script setup lang="ts">
import { useToastStore } from '../composables/useToast'
import { CheckCircle, XCircle, AlertTriangle, Info } from 'lucide-vue-next'

const toastStore = useToastStore()
</script>

<template>
  <div class="toast-container">
    <div v-for="(toast, index) in toastStore.toasts" :key="index"
      class="toast-item"
      :class="{
        'toast-success': toast.type === 'success',
        'toast-error': toast.type === 'error',
        'toast-warning': toast.type === 'warning',
        'toast-info': toast.type === 'info',
      }"
      role="alert">
      <CheckCircle v-if="toast.type === 'success'" class="w-4 h-4 flex-shrink-0" />
      <XCircle v-else-if="toast.type === 'error'" class="w-4 h-4 flex-shrink-0" />
      <AlertTriangle v-else-if="toast.type === 'warning'" class="w-4 h-4 flex-shrink-0" />
      <Info v-else class="w-4 h-4 flex-shrink-0" />
      <span class="flex-1">{{ toast.message }}</span>
      <button @click="toastStore.remove(index)" class="btn-close" aria-label="Close">
        &times;
      </button>
    </div>
  </div>
</template>

<style scoped>
.toast-container {
  position: fixed;
  top: 1rem;
  left: 0;
  right: 0;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 0 1rem;
}
.toast-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-radius: 0.375rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  font-size: 0.875rem;
  animation: fadeIn 0.2s ease-out;
  max-width: 28rem;
  width: 100%;
}
.toast-success {
  background: #f0fdf4;
  color: #166534;
  border: 1px solid #bbf7d0;
}
.toast-error {
  background: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
}
.toast-warning {
  background: #fefce8;
  color: #854d0e;
  border: 1px solid #fef08a;
}
.toast-info {
  background: #eff6ff;
  color: #1e40af;
  border: 1px solid #bfdbfe;
}
.btn-close {
  background: none;
  border: none;
  color: inherit;
  opacity: 0.5;
  cursor: pointer;
  font-size: 1.2rem;
  padding: 0;
  line-height: 1;
}
.btn-close:hover {
  opacity: 0.8;
}
@keyframes fadeIn {
  from {
    transform: translateY(-0.5rem);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
</style>
