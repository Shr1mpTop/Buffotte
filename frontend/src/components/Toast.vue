<template>
  <Teleport to="body">
    <Transition name="toast">
      <div v-if="visible" class="toast-container" :class="type">
        <div class="toast-icon">{{ icon }}</div>
        <div class="toast-message">{{ message }}</div>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
import { ref, watch } from 'vue'

export default {
  name: 'Toast',
  props: {
    message: { type: String, default: '' },
    type: { type: String, default: 'success' }, // success, error, info
    duration: { type: Number, default: 2000 }
  },
  setup(props) {
    const visible = ref(false)
    const icon = ref('✓')

    watch(() => props.message, (newVal) => {
      if (newVal) {
        visible.value = true
        icon.value = props.type === 'success' ? '✓' : props.type === 'error' ? '✕' : 'ⓘ'
        setTimeout(() => {
          visible.value = false
        }, props.duration)
      }
    }, { immediate: true })

    return { visible, icon }
  }
}
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 24px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 24px;
  background: rgba(0, 0, 0, 0.95);
  border: 1px solid rgba(0, 255, 127, 0.3);
  border-radius: 6px;
  color: var(--primary-green);
  font-family: 'Source Code Pro', monospace;
  font-size: 14px;
  z-index: 9999;
  box-shadow: 0 4px 20px rgba(0, 255, 127, 0.2);
  backdrop-filter: blur(10px);
}

.toast-container.success {
  border-color: rgba(0, 255, 127, 0.5);
}

.toast-container.error {
  border-color: rgba(255, 107, 107, 0.5);
  color: #ff6b6b;
}

.toast-container.info {
  border-color: rgba(0, 204, 255, 0.5);
  color: #00ccff;
}

.toast-icon {
  font-size: 18px;
  font-weight: 700;
}

.toast-message {
  font-weight: 500;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px);
}
</style>
