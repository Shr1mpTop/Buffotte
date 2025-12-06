<template>
  <TerminalWindow title="user@buffotte:~/kline">
    <div class="kline-console">
      <div class="line">K线数据页面（占位）</div>
      <div class="line">将显示历史行情和图表</div>
      <div class="actions"><router-link class="btn" to="/home">返回</router-link></div>
    </div>
  </TerminalWindow>
</template>

<script>
import TerminalWindow from '../components/TerminalWindow.vue'
export default { name: 'Kline', components: { TerminalWindow } }
</script>

<style scoped>
.line { margin: 8px 0 }
.actions { margin-top:12px }
.btn { padding:8px 12px; border-radius:6px; background:linear-gradient(45deg,var(--primary-green),var(--secondary-green)); border:none }
</style>
