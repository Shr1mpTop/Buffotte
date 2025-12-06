<template>
  <TerminalWindow title="user@buffotte:~/home">
    <div class="home-console">
      <pre class="welcome">Buffotte 仪表盘</pre>
      <div class="controls">
        <router-link class="btn" to="/profile">查看资料</router-link>
        <router-link class="btn" to="/kline">K线数据</router-link>
      </div>
    </div>
  </TerminalWindow>
</template>

<script>
import TerminalWindow from '../components/TerminalWindow.vue'
export default { name: 'Home', components: { TerminalWindow } }
</script>

<style scoped>
.welcome { color: var(--secondary-green); font-weight:700 }
.controls { display:flex; gap:8px; margin-top:12px }
.btn { padding:8px 12px; background:linear-gradient(45deg,var(--primary-green),var(--secondary-green)); border-radius:6px; color:#000 }
</style>
