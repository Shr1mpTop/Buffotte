<template>
  <section class="stats-section">
    <div class="stat-card">
      <div class="stat-icon">📊</div>
      <div class="stat-content">
        <h3>总物品数</h3>
        <div class="stat-value">{{ stats.total_items.toLocaleString() }}</div>
        <div class="stat-trend">+12.5%</div>
      </div>
    </div>
    <div class="stat-card">
      <div class="stat-icon">💰</div>
      <div class="stat-content">
        <h3>平均价格</h3>
        <div class="stat-value">¥{{ stats.average_price.toFixed(2) }}</div>
        <div class="stat-trend">+5.2%</div>
      </div>
    </div>
    <div class="stat-card">
      <div class="stat-icon">📈</div>
      <div class="stat-content">
        <h3>市场活跃度</h3>
        <div class="stat-value">高</div>
        <div class="stat-trend">↗️</div>
      </div>
    </div>
  </section>
</template>

<script>
export default {
  name: 'StatsSection',
  props: {
    stats: {
      type: Object,
      default: () => ({
        total_items: 0,
        average_price: 0
      })
    }
  }
}
</script>

<style scoped>
/* 统计卡片区域 */
.stats-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  margin-bottom: 3rem;
}

.stat-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #00ff88, #00aaff);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(0, 255, 136, 0.1);
}

.stat-icon {
  font-size: 2.5rem;
  opacity: 0.8;
}

.stat-content h3 {
  font-size: 0.9rem;
  color: #888;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 0.3rem;
}

.stat-trend {
  font-size: 0.8rem;
  color: #00ff88;
  font-weight: 600;
}
</style>