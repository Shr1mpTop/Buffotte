<template>
  <router-view v-slot="{ Component }">
    <transition name="page" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>
  <Toast :key="toastKey" :message="toastMessage" :type="toastType" />
</template>

<script>
import Toast from './components/Toast.vue'
import { useToast } from './composables/useToast'

export default { 
  name: 'App', 
  components: { Toast },
  setup() {
    const { toastMessage, toastType, toastKey } = useToast()
    return { toastMessage, toastType, toastKey }
  }
}
</script>

<style>
:root { --primary-green: #00ff8b; --secondary-green: #8affc9 }
html,body { width: 100%; height:100%; background:#000; color:var(--primary-green); font-family: 'Source Code Pro', monospace; margin: 0; padding: 0; overflow: hidden; }
#app { width: 100%; height:100%; overflow: hidden; background: #000; }
* { box-sizing: border-box; }

/* 页面过渡动画 */
.page-enter-active,
.page-leave-active {
  transition: all 0.3s ease;
}

.page-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.page-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}
</style>
