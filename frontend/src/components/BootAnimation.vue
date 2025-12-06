<template>
  <div v-if="show" class="boot-screen">
    <div class="boot-content">
      <div class="boot-logo">BUFFOTTE</div>
      <div class="boot-text">
        <div class="boot-line" v-for="(line, index) in bootLines" :key="index" :style="{ animationDelay: index * 0.1 + 's' }">
          {{ line }}
        </div>
      </div>
      <div class="loading-bar">
        <div class="loading-progress"></div>
      </div>
      <div class="boot-status">{{ status }}</div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'

export default {
  name: 'BootAnimation',
  emits: ['complete'],
  setup(props, { emit }) {
    const show = ref(true)
    const status = ref('INITIALIZING...')
    
    const bootLines = [
      '> System boot sequence initiated...',
      '> Loading kernel modules...',
      '> Initializing user interface...',
      '> Establishing secure connection...',
      '> Loading dashboard components...',
      '> System ready.'
    ]

    onMounted(() => {
      setTimeout(() => {
        status.value = 'LOADING...'
      }, 800)

      setTimeout(() => {
        status.value = 'READY'
      }, 1800)

      setTimeout(() => {
        show.value = false
        emit('complete')
      }, 2400)
    })

    return { show, bootLines, status }
  }
}
</script>

<style scoped>
.boot-screen {
  position: fixed;
  inset: 0;
  background: #000;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeOut 0.5s ease 2s forwards;
}

@keyframes fadeOut {
  to {
    opacity: 0;
  }
}

.boot-content {
  max-width: 600px;
  width: 100%;
  padding: 40px;
}

.boot-logo {
  color: var(--primary-green);
  font-size: 48px;
  font-weight: 700;
  letter-spacing: 8px;
  text-align: center;
  margin-bottom: 40px;
  text-shadow: 0 0 30px rgba(0, 255, 127, 0.8);
  animation: glowPulse 1.5s ease-in-out infinite;
}

@keyframes glowPulse {
  0%, 100% {
    text-shadow: 0 0 30px rgba(0, 255, 127, 0.8);
  }
  50% {
    text-shadow: 0 0 50px rgba(0, 255, 127, 1), 0 0 60px rgba(0, 255, 127, 0.6);
  }
}

.boot-text {
  margin-bottom: 30px;
}

.boot-line {
  color: rgba(0, 255, 127, 0.8);
  font-size: 14px;
  margin: 8px 0;
  opacity: 0;
  animation: typeLine 0.3s ease forwards;
}

@keyframes typeLine {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.loading-bar {
  width: 100%;
  height: 4px;
  background: rgba(0, 255, 127, 0.1);
  border-radius: 2px;
  overflow: hidden;
  margin: 20px 0;
}

.loading-progress {
  height: 100%;
  background: linear-gradient(90deg, var(--primary-green), var(--secondary-green));
  width: 0;
  animation: loadProgress 2s ease forwards;
  box-shadow: 0 0 10px rgba(0, 255, 127, 0.8);
}

@keyframes loadProgress {
  0% { width: 0; }
  20% { width: 15%; }
  40% { width: 35%; }
  60% { width: 60%; }
  80% { width: 85%; }
  100% { width: 100%; }
}

.boot-status {
  color: var(--secondary-green);
  font-size: 12px;
  text-align: center;
  margin-top: 15px;
  letter-spacing: 2px;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
</style>
