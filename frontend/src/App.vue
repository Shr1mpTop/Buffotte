<template>
  <div id="app">
    <!-- 顶部标题栏 -->
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

    <!-- 主要内容区域 -->
    <main class="main-content">
      <!-- 统计卡片 -->
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

      <!-- K线图区域 -->
      <section class="chart-section">
        <div class="chart-header">
          <h2>价格K线图</h2>
          <div class="chart-controls">
            <select v-model="selectedKlineType" @change="fetchKlineData" class="time-selector">
              <option value="hour">小时K</option>
              <option value="day">日K</option>
              <option value="week">周K</option>
            </select>
            <button @click="refreshData" class="refresh-btn">🔄 刷新数据</button>
          </div>
        </div>
        <div class="chart-container">
          <canvas ref="klineCanvas" class="kline-chart"></canvas>
          <div class="chart-overlay" v-if="loading">
            <div class="loading-spinner"></div>
            <span>加载中...</span>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'App',
  data() {
    return {
      stats: {
        total_items: 0,
        average_price: 0
      },
      klineData: [],
      selectedKlineType: 'hour',
      loading: false,
      lastUpdate: new Date().toLocaleTimeString('zh-CN')
    }
  },
  mounted() {
    this.fetchStats()
    this.fetchKlineData()
    // 每30秒自动更新一次数据
    setInterval(() => {
      this.fetchStats()
      this.fetchKlineData()
    }, 30000)
  },
  methods: {
    async fetchStats() {
      try {
        const response = await axios.get('/api/stats')
        this.stats = response.data
        this.lastUpdate = new Date().toLocaleTimeString('zh-CN')
      } catch (error) {
        console.error('Error fetching stats:', error)
      }
    },
    async fetchKlineData() {
      this.loading = true
      try {
        const response = await axios.get(`/api/kline/${this.selectedKlineType}`)
        // 确保价格字段是数字类型
        this.klineData = response.data.map(item => ({
          ...item,
          open_price: parseFloat(item.open_price) || 0,
          high_price: parseFloat(item.high_price) || 0,
          low_price: parseFloat(item.low_price) || 0,
          close_price: parseFloat(item.close_price) || 0,
          volume: parseInt(item.volume) || 0,
          turnover: parseFloat(item.turnover) || 0
        }))
        this.drawKlineChart()
        this.lastUpdate = new Date().toLocaleTimeString('zh-CN')
      } catch (error) {
        console.error('Error fetching kline data:', error)
      } finally {
        this.loading = false
      }
    },
    // 刷新数据 - 调用爬虫更新数据库
    async refreshData() {
      try {
        this.loading = true
        const response = await axios.post('/api/refresh')
        console.log('数据刷新响应:', response.data)

        // 等待几秒后重新获取数据
        setTimeout(() => {
          this.fetchStats()
          this.fetchKlineData()
        }, 2000)

        // 显示成功消息
        alert('数据刷新已启动！请稍后查看最新数据。')
      } catch (error) {
        console.error('Error refreshing data:', error)
        alert('数据刷新失败，请稍后重试。')
      } finally {
        this.loading = false
      }
    },
    // 时间戳转换函数 - 数据库已经是北京时间，直接转换
    formatTimestamp(timestamp) {
      // 数据库中已经是北京时间，直接转换为毫秒
      const date = new Date(timestamp * 1000);
      const now = new Date();
      const diff = now - date;

      if (diff < 60000) { // 1分钟内
        return '刚刚'
      } else if (diff < 3600000) { // 1小时内
        return `${Math.floor(diff / 60000)}分钟前`
      } else if (diff < 86400000) { // 1天内
        return `${Math.floor(diff / 3600000)}小时前`
      } else if (diff < 604800000) { // 7天内
        return `${Math.floor(diff / 86400000)}天前`
      } else {
        // 显示具体的北京时间
        return date.toLocaleString('zh-CN', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          hour12: false
        });
      }
    },
    drawKlineChart() {
      const canvas = this.$refs.klineCanvas
      if (!canvas) {
        console.error('Canvas element not found')
        return
      }

      const ctx = canvas.getContext('2d')
      if (!ctx) {
        console.error('Failed to get canvas context')
        return
      }

      // 设置画布尺寸
      const container = canvas.parentElement
      canvas.width = container.clientWidth
      canvas.height = 500

      // 清除画布
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      if (this.klineData.length === 0) {
        ctx.fillStyle = '#666'
        ctx.font = '16px Arial'
        ctx.textAlign = 'center'
        ctx.fillText('暂无数据', canvas.width / 2, canvas.height / 2)
        return
      }

      // 找到价格范围（增加一些边距）
      const prices = this.klineData.flatMap(item => [item.open_price, item.high_price, item.low_price, item.close_price])
      const minPrice = Math.min(...prices) * 0.995
      const maxPrice = Math.max(...prices) * 1.005
      const priceRange = maxPrice - minPrice

      const width = canvas.width - 80 // 左侧留出Y轴空间
      const height = canvas.height - 60 // 底部留出X轴空间
      const barWidth = Math.max(2, width / this.klineData.length * 0.8)

      // 绘制网格线
      ctx.strokeStyle = '#333'
      ctx.lineWidth = 1

      // 水平网格线
      for (let i = 0; i <= 5; i++) {
        const y = 30 + (height / 5) * i
        ctx.beginPath()
        ctx.moveTo(60, y)
        ctx.lineTo(canvas.width - 20, y)
        ctx.stroke()

        // 价格标签
        const price = maxPrice - (priceRange / 5) * i
        ctx.fillStyle = '#999'
        ctx.font = '12px Arial'
        ctx.textAlign = 'right'
        ctx.fillText(`¥${price.toFixed(2)}`, 55, y + 4)
      }

      // 绘制K线 - 从右到左绘制（最新的在右侧）
      this.klineData.forEach((item, index) => {
        // 反转索引：最新的数据在右侧
        const reversedIndex = this.klineData.length - 1 - index;
        const x = 70 + reversedIndex * (width / this.klineData.length);
        const open = 30 + (maxPrice - item.open_price) / priceRange * height;
        const close = 30 + (maxPrice - item.close_price) / priceRange * height;
        const high = 30 + (maxPrice - item.high_price) / priceRange * height;
        const low = 30 + (maxPrice - item.low_price) / priceRange * height;

        // 绘制高低线
        ctx.beginPath();
        ctx.moveTo(x + barWidth / 2, high);
        ctx.lineTo(x + barWidth / 2, low);
        ctx.strokeStyle = item.close_price > item.open_price ? '#00ff88' : '#ff4444';
        ctx.lineWidth = 1;
        ctx.stroke();

        // 绘制开盘收盘矩形
        const color = item.close_price > item.open_price ? '#00ff88' : '#ff4444';
        ctx.fillStyle = color;
        const rectHeight = Math.abs(close - open);
        ctx.fillRect(x, Math.min(open, close), barWidth, rectHeight || 1);

        // 绘制边框
        ctx.strokeStyle = color;
        ctx.lineWidth = 1;
        ctx.strokeRect(x, Math.min(open, close), barWidth, rectHeight || 1);
      });

      // 绘制X轴时间标签
      ctx.fillStyle = '#999'
      ctx.font = '12px Arial'
      ctx.textAlign = 'center'

      const labelCount = Math.min(10, this.klineData.length)
      for (let i = 0; i < labelCount; i++) {
        // 反转标签顺序：最新的在右侧
        const reversedIndex = Math.floor((this.klineData.length / labelCount) * (labelCount - 1 - i))
        const item = this.klineData[reversedIndex]
        const x = 70 + (this.klineData.length - 1 - reversedIndex) * (width / this.klineData.length) + barWidth / 2
        const y = canvas.height - 20

        // 显示简化的北京时间格式（已经是北京时间）
        const date = new Date(item.timestamp * 1000);
        const timeStr = date.toLocaleString('zh-CN', {
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          hour12: false
        });

        ctx.fillText(timeStr, x, y)
      }

      // 添加鼠标事件监听器用于显示详细信息
      this.addMouseEvents(canvas, width, height, barWidth, maxPrice, priceRange)
    },
    // 添加鼠标事件监听器
    addMouseEvents(canvas, width, height, barWidth, maxPrice, priceRange) {
      const ctx = canvas.getContext('2d')
      const tooltip = document.createElement('div')
      tooltip.className = 'kline-tooltip'
      tooltip.style.cssText = `
        position: absolute;
        background: rgba(0, 0, 0, 0.9);
        color: #ffffff;
        padding: 12px;
        border-radius: 8px;
        font-size: 12px;
        font-family: Arial, sans-serif;
        pointer-events: none;
        z-index: 1000;
        border: 1px solid #00ff88;
        box-shadow: 0 4px 16px rgba(0, 255, 136, 0.2);
        display: none;
      `
      document.body.appendChild(tooltip)

      canvas.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect()
        const mouseX = e.clientX - rect.left
        const mouseY = e.clientY - rect.top

        // 检查鼠标是否在K线区域内
        if (mouseX >= 70 && mouseX <= 70 + width && mouseY >= 30 && mouseY <= 30 + height) {
          // 计算鼠标所在的K线索引
          const index = Math.floor((mouseX - 70) / (width / this.klineData.length))
          const reversedIndex = this.klineData.length - 1 - index

          if (reversedIndex >= 0 && reversedIndex < this.klineData.length) {
            const item = this.klineData[reversedIndex]

            // 格式化时间
            const date = new Date(item.timestamp * 1000)
            const timeStr = date.toLocaleString('zh-CN', {
              year: 'numeric',
              month: '2-digit',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit',
              hour12: false
            })

            // 显示详细信息
            tooltip.innerHTML = `
              <div style="font-weight: bold; color: #00ff88; margin-bottom: 8px;">${timeStr}</div>
              <div>开盘价: <span style="color: #ffffff;">¥${(item.open_price || 0).toFixed(2)}</span></div>
              <div>收盘价: <span style="color: ${item.close_price > item.open_price ? '#00ff88' : '#ff4444'};">¥${(item.close_price || 0).toFixed(2)}</span></div>
              <div>最高价: <span style="color: #ffaa44;">¥${(item.high_price || 0).toFixed(2)}</span></div>
              <div>最低价: <span style="color: #44aaff;">¥${(item.low_price || 0).toFixed(2)}</span></div>
              <div>成交量: <span style="color: #ff88aa;">${item.volume || 'N/A'}</span></div>
              <div>涨跌幅: <span style="color: ${item.close_price > item.open_price ? '#00ff88' : '#ff4444'}; font-weight: bold;">
                ${item.open_price > 0 ? ((item.close_price - item.open_price) / item.open_price * 100).toFixed(2) : '0.00'}%
              </span></div>
            `

            tooltip.style.left = `${e.clientX + 10}px`
            tooltip.style.top = `${e.clientY - 10}px`
            tooltip.style.display = 'block'
          }
        } else {
          tooltip.style.display = 'none'
        }
      })

      canvas.addEventListener('mouseleave', () => {
        tooltip.style.display = 'none'
      })
    }
  }
}
</script>

<style>
/* 全局样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  background: #0a0a0a;
  color: #ffffff;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  overflow-x: hidden;
}

/* 应用容器 */
#app {
  min-height: 100vh;
  background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
}

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

/* 主要内容区域 */
.main-content {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

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

/* 图表区域 */
.chart-section {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 2rem;
  position: relative;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.chart-header h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: #ffffff;
}

.chart-controls {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.time-selector {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  color: #ffffff;
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.time-selector:focus {
  outline: none;
  border-color: #00ff88;
  box-shadow: 0 0 0 2px rgba(0, 255, 136, 0.2);
}

.refresh-btn {
  background: linear-gradient(45deg, #00ff88, #00aaff);
  border: none;
  border-radius: 8px;
  color: #000;
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.refresh-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 16px rgba(0, 255, 136, 0.3);
}

/* 图表容器 */
.chart-container {
  position: relative;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 12px;
  padding: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.kline-chart {
  width: 100%;
  height: 500px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.5);
}

/* 加载覆盖层 */
.chart-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  color: #ffffff;
  font-size: 1.1rem;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top: 3px solid #00ff88;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* K线图tooltip样式 */
.kline-tooltip {
  position: absolute;
  background: rgba(0, 0, 0, 0.95) !important;
  color: #ffffff !important;
  padding: 12px !important;
  border-radius: 8px !important;
  font-size: 12px !important;
  font-family: 'Segoe UI', Arial, sans-serif !important;
  pointer-events: none !important;
  z-index: 1000 !important;
  border: 1px solid #00ff88 !important;
  box-shadow: 0 4px 16px rgba(0, 255, 136, 0.3) !important;
  backdrop-filter: blur(10px) !important;
  max-width: 200px !important;
  white-space: nowrap !important;
}

.kline-tooltip div {
  margin-bottom: 4px !important;
}

.kline-tooltip div:last-child {
  margin-bottom: 0 !important;
}
</style>