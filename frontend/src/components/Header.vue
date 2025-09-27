<template>
  <header class="header">
    <div class="logo">
      <h1>🎮 Buffotte</h1>
      <span class="subtitle">CS:GO饰品价格分析系统</span>
    </div>
    <div class="status">
      <div class="status-item">
        <span class="label">数据状态</span>
        <span class="value online">● 在线</span>
      </div>
      <div class="status-item">
        <span class="label">最后更新</span>
        <span class="value">{{ lastUpdate }}</span>
      </div>
    </div>
  </header>
</template>

<script>
export default {
  name: 'Header',
  props: {
    lastUpdate: {
      type: String,
      default: ''
    }
  }
}
</script>

<style scoped>
/* 顶部标题栏 */
.header {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 100;
}

.logo h1 {
  font-size: 1.8rem;
  font-weight: 700;
  background: linear-gradient(45deg, #00ff88, #00aaff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 0.2rem;
}

.logo .subtitle {
  font-size: 0.9rem;
  color: #888;
  font-weight: 400;
}

.status {
  display: flex;
  gap: 2rem;
}

.status-item {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.status-item .label {
  font-size: 0.8rem;
  color: #888;
  margin-bottom: 0.2rem;
}

.status-item .value {
  font-size: 0.9rem;
  font-weight: 500;
}

.status-item .value.online {
  color: #00ff88;
}
</style>