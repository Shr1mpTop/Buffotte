<template>
  <section class="chart-section">
    <div class="chart-header">
      <h2>价格K线图</h2>
      <div class="chart-controls">
        <select :value="localSelectedType" @change="handleTypeChange" class="time-selector">
          <option value="hour">小时K</option>
          <option value="day">日K</option>
          <option value="week">周K</option>
        </select>
        <button @click="$emit('refresh-data')" class="refresh-btn">🔄 刷新数据</button>
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
</template>

<script>
export default {
  name: 'KlineChart',
  props: {
    klineData: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    },
    selectedKlineType: {
      type: String,
      default: 'hour'
    }
  },
  data() {
    return {
      localSelectedType: this.selectedKlineType
    }
  },
  watch: {
    selectedKlineType: {
      handler(newVal) {
        this.localSelectedType = newVal
      },
      immediate: true
    },
    klineData: {
      handler() {
        this.$nextTick(() => {
          this.drawKlineChart()
        })
      },
      deep: true
    }
  },
  mounted() {
    this.$nextTick(() => {
      this.drawKlineChart()
    })
  },
  methods: {
    handleTypeChange(event) {
      const newType = event.target.value
      this.localSelectedType = newType
      this.$emit('kline-type-change', newType)
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

      // 找到成交量范围
      const volumes = this.klineData.map(item => item.volume || 0)
      const maxVolume = Math.max(...volumes)
      const minVolume = Math.min(...volumes)
      const volumeRange = maxVolume - minVolume

      const width = canvas.width - 80 // 左侧留出Y轴空间
      const height = canvas.height - 60 // 底部留出X轴空间
      const volumeHeight = 80 // 成交量区域高度
      const klineHeight = height - volumeHeight - 20 // K线区域高度，留出间距
      const barWidth = Math.max(2, width / this.klineData.length * 0.8) // K线柱子宽度

      // 绘制网格线
      ctx.strokeStyle = '#333'
      ctx.lineWidth = 1

      // 水平网格线（只在K线区域绘制）
      for (let i = 0; i <= 5; i++) {
        const y = 30 + (klineHeight / 5) * i
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
        const open = 30 + (maxPrice - item.open_price) / priceRange * klineHeight;
        const close = 30 + (maxPrice - item.close_price) / priceRange * klineHeight;
        const high = 30 + (maxPrice - item.high_price) / priceRange * klineHeight;
        const low = 30 + (maxPrice - item.low_price) / priceRange * klineHeight;

        // 绘制高低线
        ctx.beginPath();
        ctx.moveTo(x + barWidth / 2, high);
        ctx.lineTo(x + barWidth / 2, low);
        ctx.strokeStyle = item.close_price > item.open_price ? '#ff4444' : '#00ff88';
        ctx.lineWidth = 1;
        ctx.stroke();

        // 绘制开盘收盘矩形
        const color = item.close_price > item.open_price ? '#ff4444' : '#00ff88';
        ctx.fillStyle = color;
        const rectHeight = Math.abs(close - open);
        ctx.fillRect(x, Math.min(open, close), barWidth, rectHeight || 1);

        // 绘制边框
        ctx.strokeStyle = color;
        ctx.lineWidth = 1;
        ctx.strokeRect(x, Math.min(open, close), barWidth, rectHeight || 1);

        // 绘制成交量柱状图
        const volumeY = 30 + klineHeight + 20; // 成交量区域起始Y坐标
        const volumeBarHeight = volumeRange > 0 ? ((item.volume || 0) / maxVolume) * (volumeHeight - 20) : 0;
        const volumeColor = item.close_price > item.open_price ? '#ff4444' : '#00ff88';

        ctx.fillStyle = volumeColor;
        ctx.fillRect(x, volumeY + (volumeHeight - 20 - volumeBarHeight), barWidth, volumeBarHeight);

        // 成交量柱子边框
        ctx.strokeStyle = volumeColor;
        ctx.lineWidth = 1;
        ctx.strokeRect(x, volumeY + (volumeHeight - 20 - volumeBarHeight), barWidth, volumeBarHeight);
      });

      // 成交量区域Y轴标签
      ctx.fillStyle = '#999'
      ctx.font = '12px Arial'
      ctx.textAlign = 'right'
      for (let i = 0; i <= 3; i++) {
        const volumeY = 30 + klineHeight + 20 + (volumeHeight - 20) * (1 - i / 3)
        const volumeValue = Math.round(maxVolume * (i / 3))
        ctx.fillText(volumeValue.toString(), 55, volumeY + 4)
      }
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

        // 显示简化的北京时间格式（数据库已经是北京时间）
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
      this.addMouseEvents(canvas, width, height, barWidth, maxPrice, priceRange, klineHeight, volumeHeight, maxVolume)
    },
    // 添加鼠标事件监听器
    addMouseEvents(canvas, width, height, barWidth, maxPrice, priceRange, klineHeight, volumeHeight, maxVolume) {
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
        if (mouseX >= 70 && mouseX <= 70 + width && mouseY >= 30 && mouseY <= 30 + klineHeight) {
          // 计算鼠标所在的K线索引
          const index = Math.floor((mouseX - 70) / (width / this.klineData.length))
          const reversedIndex = this.klineData.length - 1 - index

          if (reversedIndex >= 0 && reversedIndex < this.klineData.length) {
            const item = this.klineData[reversedIndex]
            // 获取前一个周期的收盘价用于计算日涨幅（数组是降序排列，索引越大时间越早）
            const prevItem = reversedIndex < this.klineData.length - 1 ? this.klineData[reversedIndex + 1] : null
            const prevClosePrice = prevItem ? prevItem.close_price : item.open_price

            // 计算日涨幅
            const dayChangePercent = prevClosePrice > 0 ? ((item.close_price - prevClosePrice) / prevClosePrice * 100) : 0

            // 格式化时间（数据库已经是北京时间）
            const date = new Date(item.timestamp * 1000)
            const timeStr = date.toLocaleString('zh-CN', {
              year: 'numeric',
              month: '2-digit',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit',
              hour12: false
            })

            // 显示完整详细信息
            tooltip.innerHTML = `
              <div style="font-weight: bold; color: #00ff88; margin-bottom: 8px;">${timeStr}</div>
              <div>开盘价: <span style="color: #ffffff;">¥${(item.open_price || 0).toFixed(2)}</span></div>
              <div>收盘价: <span style="color: ${item.close_price > item.open_price ? '#00ff88' : '#ff4444'};">¥${(item.close_price || 0).toFixed(2)}</span></div>
              <div>最高价: <span style="color: #ffaa44;">¥${(item.high_price || 0).toFixed(2)}</span></div>
              <div>最低价: <span style="color: #44aaff;">¥${(item.low_price || 0).toFixed(2)}</span></div>
              <div>成交量: <span style="color: #ff88aa;">${item.volume || 'N/A'}</span></div>
              <div>涨跌幅: <span style="color: ${dayChangePercent >= 0 ? '#ff4444' : '#00ff88'}; font-weight: bold;">
                ${dayChangePercent.toFixed(2)}%
              </span></div>
            `

            tooltip.style.left = `${e.clientX + 10}px`
            tooltip.style.top = `${e.clientY - 10}px`
            tooltip.style.display = 'block'
          }
        }
        // 检查鼠标是否在成交量区域内
        else if (mouseX >= 70 && mouseX <= 70 + width && mouseY >= 30 + klineHeight + 20 && mouseY <= 30 + klineHeight + 20 + volumeHeight) {
          // 计算鼠标所在的K线索引
          const index = Math.floor((mouseX - 70) / (width / this.klineData.length))
          const reversedIndex = this.klineData.length - 1 - index

          if (reversedIndex >= 0 && reversedIndex < this.klineData.length) {
            const item = this.klineData[reversedIndex]
            // 获取前一个周期的收盘价用于计算日涨幅（数组是降序排列，索引越大时间越早）
            const prevItem = reversedIndex < this.klineData.length - 1 ? this.klineData[reversedIndex + 1] : null
            const prevClosePrice = prevItem ? prevItem.close_price : item.open_price

            // 计算日涨幅
            const dayChangePercent = prevClosePrice > 0 ? ((item.close_price - prevClosePrice) / prevClosePrice * 100) : 0

            // 格式化时间（数据库已经是北京时间）
            const date = new Date(item.timestamp * 1000)
            const timeStr = date.toLocaleString('zh-CN', {
              year: 'numeric',
              month: '2-digit',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit',
              hour12: false
            })

            // 显示完整详细信息
            tooltip.innerHTML = `
              <div style="font-weight: bold; color: #00ff88; margin-bottom: 8px;">${timeStr}</div>
              <div>开盘价: <span style="color: #ffffff;">¥${(item.open_price || 0).toFixed(2)}</span></div>
              <div>收盘价: <span style="color: ${item.close_price > item.open_price ? '#00ff88' : '#ff4444'};">¥${(item.close_price || 0).toFixed(2)}</span></div>
              <div>最高价: <span style="color: #ffaa44;">¥${(item.high_price || 0).toFixed(2)}</span></div>
              <div>最低价: <span style="color: #44aaff;">¥${(item.low_price || 0).toFixed(2)}</span></div>
              <div>成交量: <span style="color: #ff88aa;">${item.volume || 'N/A'}</span></div>
              <div>涨跌幅: <span style="color: ${dayChangePercent >= 0 ? '#ff4444' : '#00ff88'}; font-weight: bold;">
                ${dayChangePercent.toFixed(2)}%
              </span></div>
            `

            tooltip.style.left = `${e.clientX + 10}px`
            tooltip.style.top = `${e.clientY - 10}px`
            tooltip.style.display = 'block'
          }
        }
        else {
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

<style scoped>
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