<template>
  <div id="app">
    <MatrixBackground />
    <router-view />
    <Toast :key="toastKey" :message="toastMessage" :type="toastType" />
  </div>
</template>

<script>
import MatrixBackground from './components/MatrixBackground.vue'
import Toast from './components/Toast.vue'
import { useToast } from './composables/useToast'

export default { 
  name: 'App', 
  components: { MatrixBackground, Toast },
  setup() {
    const { toastMessage, toastType, toastKey } = useToast()
    return { toastMessage, toastType, toastKey }
  }
}
</script>

<style>
:root { --primary-green: #00ff8b; --secondary-green: #8affc9 }
html,body { height:100%; background:#000; color:var(--primary-green); font-family: 'Source Code Pro', monospace; margin: 0; padding: 0; overflow-x: hidden; }
#app { height:100%; }
* { box-sizing: border-box; }
</style>
