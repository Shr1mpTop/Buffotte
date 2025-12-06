<template>
  <div id="app">
    <MatrixBackground />
    <div class="app-shell">
      <router-view />
    </div>
  </div>
</template>

<script>
import MatrixBackground from './components/MatrixBackground.vue'
export default { name: 'App', components: { MatrixBackground } }
</script>

<style>
:root { --primary-green: #00ff8b; --secondary-green: #8affc9 }
html,body,#app { height:100%; background:#000; color:var(--primary-green); font-family: 'Source Code Pro', monospace }
.app-shell { display:flex; align-items:center; justify-content:center; min-height:100vh; padding:24px }
</style>
