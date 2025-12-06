import { ref } from 'vue'

const toastMessage = ref('')
const toastType = ref('success')
const toastKey = ref(0)

export function useToast() {
  const showToast = (message, type = 'success') => {
    toastMessage.value = message
    toastType.value = type
    toastKey.value++
  }

  const success = (message) => showToast(message, 'success')
  const error = (message) => showToast(message, 'error')
  const info = (message) => showToast(message, 'info')

  return {
    toastMessage,
    toastType,
    toastKey,
    success,
    error,
    info
  }
}
