<template>
  <div id="app">
    <!-- 顶部标题栏 -->
    <Header :last-update="lastUpdate" />

    <!-- 主要内容区域 -->
    <main class="main-content">
      <!-- 统计卡片 -->
      <StatsSection :stats="stats" />

      <!-- K线图区域 -->
      <KlineChart
        :kline-data="klineData"
        :loading="loading"
        :selected-kline-type="selectedKlineType"
        @kline-type-change="handleKlineTypeChange"
        @refresh-data="refreshData"
      />
    </main>
  </div>
</template>

<script>
import axios from 'axios'
import Header from './components/Header.vue'
import StatsSection from './components/StatsSection.vue'
import KlineChart from './components/KlineChart.vue'

export default {
  name: 'App',
  components: {
    Header,
    StatsSection,
    KlineChart
  },
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
        this.lastUpdate = new Date().toLocaleTimeString('zh-CN')
      } catch (error) {
        console.error('Error fetching kline data:', error)
      } finally {
        this.loading = false
      }
    },
    handleKlineTypeChange(newType) {
      this.selectedKlineType = newType
      this.fetchKlineData()
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
        console.log('数据刷新已启动！请稍后查看最新数据。')
      } catch (error) {
        console.error('Error refreshing data:', error)
        console.log('数据刷新失败，请稍后重试。')
      } finally {
        this.loading = false
      }
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

/* 主要内容区域 */
.main-content {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}
</style>
