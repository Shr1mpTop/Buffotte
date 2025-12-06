<template>
  <div class="terminal-window">
    <div class="terminal-header">
      <div class="terminal-buttons">
        <span class="terminal-button close"></span>
        <span class="terminal-button minimize"></span>
        <span class="terminal-button maximize"></span>
      </div>
      <div class="terminal-title">{{ title }}</div>
    </div>
    <div class="terminal-body">
      <slot />
    </div>
  </div>
</template>

<script>
export default {
  name: 'TerminalWindow',
  props: { title: { type: String, default: 'terminal' } }
}
</script>

<style scoped>
.terminal-window { background: rgba(0,0,0,0.9); border-radius: 8px; border: 1px solid rgba(0,255,127,0.12); overflow: hidden; }
.terminal-header { display:flex; align-items:center; gap:8px; padding:12px 16px; border-bottom:1px solid rgba(0,255,127,0.03) }
.terminal-button { width:12px; height:12px; border-radius:50%; display:inline-block }
.terminal-button.close { background:#ff5f57 }
.terminal-button.minimize { background:#ffbd2e }
.terminal-button.maximize { background:#27c93f }
.terminal-title { color:var(--primary-green); font-weight:700; text-align:center; }
.terminal-body { padding:18px }
</style>
