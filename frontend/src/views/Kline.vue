<template>
  <div class="kline">
    <div class="kline-header">
      <h1 class="title">$ ./kline_monitor.sh</h1>
    </div>
    <div class="kline-content">
      <div class="placeholder-card">
        <div class="placeholder-icon">📊</div>
        <div class="placeholder-text">K线数据图表</div>
        <div class="placeholder-hint">[占位区域 - 待实现]</div>
      </div>
    </div>
  </div>
</template>

<script>
export default { name: 'Kline' }
</script>

<style scoped>
.kline {
  max-width: 1200px;
}

.kline-header {
  margin-bottom: 32px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(0, 255, 127, 0.2);
}

.title {
  color: var(--primary-green);
  font-size: 24px;
  font-weight: 700;
  margin: 0;
  text-shadow: 0 0 10px rgba(0, 255, 127, 0.3);
}

.placeholder-card {
  background: rgba(0, 0, 0, 0.6);
  border: 1px solid rgba(0, 255, 127, 0.2);
  border-radius: 6px;
  padding: 60px 40px;
  text-align: center;
}

.placeholder-icon {
  font-size: 64px;
  margin-bottom: 20px;
  opacity: 0.3;
}

.placeholder-text {
  color: var(--primary-green);
  font-size: 18px;
  margin-bottom: 8px;
}

.placeholder-hint {
  color: rgba(0, 255, 127, 0.4);
  font-size: 14px;
  font-style: italic;
}
</style>
