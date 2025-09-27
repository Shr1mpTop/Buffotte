<template>
  <div id="app">
    <h1>Buffotte Data Dashboard</h1>
    <div class="stats">
      <h2>总体数据</h2>
      <p>总物品数: {{ stats.total_items }}</p>
      <p>平均价格: {{ stats.average_price }}</p>
    </div>
    <div class="kline">
      <h2>K线图</h2>
      <canvas ref="klineCanvas" width="800" height="400"></canvas>
    </div>
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
      klineData: []
    }
  },
  mounted() {
    this.fetchStats()
    this.fetchKlineData()
  },
  methods: {
    async fetchStats() {
      try {
        const response = await axios.get('/api/stats/')
        this.stats = response.data
      } catch (error) {
        console.error('Error fetching stats:', error)
      }
    },
    async fetchKlineData() {
      try {
        const response = await axios.get('/api/kline/')
        this.klineData = response.data
        this.drawKlineChart()
      } catch (error) {
        console.error('Error fetching kline data:', error)
      }
    },
    drawKlineChart() {
      const canvas = this.$refs.klineCanvas
      const ctx = canvas.getContext('2d')
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      if (this.klineData.length === 0) return

      // 找到价格范围
      const prices = this.klineData.flatMap(item => [item.open_price, item.high_price, item.low_price, item.close_price])
      const minPrice = Math.min(...prices)
      const maxPrice = Math.max(...prices)
      const priceRange = maxPrice - minPrice

      const width = canvas.width
      const height = canvas.height
      const barWidth = width / this.klineData.length

      this.klineData.forEach((item, index) => {
        const x = index * barWidth
        const open = (maxPrice - item.open_price) / priceRange * height
        const close = (maxPrice - item.close_price) / priceRange * height
        const high = (maxPrice - item.high_price) / priceRange * height
        const low = (maxPrice - item.low_price) / priceRange * height

        // 绘制高低线
        ctx.beginPath()
        ctx.moveTo(x + barWidth / 2, high)
        ctx.lineTo(x + barWidth / 2, low)
        ctx.strokeStyle = 'black'
        ctx.stroke()

        // 绘制开盘收盘矩形
        const color = item.close_price > item.open_price ? 'green' : 'red'
        ctx.fillStyle = color
        const rectHeight = Math.abs(close - open)
        ctx.fillRect(x, Math.min(open, close), barWidth * 0.8, rectHeight || 1)
      })
    }
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
.stats, .kline {
  margin: 20px;
}
</style>