<template>
  <div id="app">
    <header class="header">
      <h1>🎮 Buffotte 饰品价格分析</h1>
      <p>实时CS:GO饰品价格分布统计</p>
    </header>

    <!-- 搜索栏 -->
    <div class="search-section">
      <SearchBox @item-selected="onItemSelected" />
    </div>

    <!-- 饰品详情 -->
    <ItemDetail 
      :item="selectedItem" 
      @item-updated="onItemUpdated"
    />

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">
      <p>正在加载数据...</p>
    </div>

    <!-- 错误状态 -->
    <div v-if="error" class="error">
      <p>{{ error }}</p>
    </div>

    <!-- 主要内容 -->
    <div v-if="!loading && !error" class="dashboard">
      <!-- 统计卡片 -->
      <div class="stats-card">
        <div class="card-title">📊 数据统计</div>
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-value">{{ stats.totalItems?.toLocaleString() || '0' }}</div>
            <div class="stat-label">总饰品数量</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">¥{{ stats.avgPrice || '0' }}</div>
            <div class="stat-label">平均价格</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">¥{{ stats.minPrice || '0' }}</div>
            <div class="stat-label">最低价格</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">¥{{ stats.maxPrice?.toLocaleString() || '0' }}</div>
            <div class="stat-label">最高价格</div>
          </div>
        </div>
      </div>

      <!-- 饼状图 -->
      <div class="chart-card">
        <div class="card-title">🥧 价格区间分布</div>
        <PriceChart :data="chartData" />
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import PriceChart from './components/PriceChart.vue'
import SearchBox from './components/SearchBox.vue'
import ItemDetail from './components/ItemDetail.vue'

export default {
  name: 'App',
  components: {
    PriceChart,
    SearchBox,
    ItemDetail
  },
  setup() {
    const loading = ref(true)
    const error = ref(null)
    const stats = ref({})
    const chartData = ref([])
    const selectedItem = ref(null)

    // 获取统计数据
    const fetchStats = async () => {
      try {
        const response = await axios.get('/api/stats')
        if (response.data.success) {
          stats.value = response.data.data
        } else {
          throw new Error(response.data.message || '获取统计数据失败')
        }
      } catch (err) {
        console.error('获取统计数据失败:', err)
        error.value = '获取统计数据失败: ' + err.message
      }
    }

    // 获取价格分布数据
    const fetchPriceDistribution = async () => {
      try {
        const response = await axios.get('/api/price-distribution')
        if (response.data.success) {
          chartData.value = response.data.data
        } else {
          throw new Error(response.data.message || '获取价格分布数据失败')
        }
      } catch (err) {
        console.error('获取价格分布数据失败:', err)
        error.value = '获取价格分布数据失败: ' + err.message
      }
    }

    // 加载所有数据
    const loadData = async () => {
      try {
        loading.value = true
        error.value = null
        
        await Promise.all([
          fetchStats(),
          fetchPriceDistribution()
        ])
      } catch (err) {
        console.error('加载数据失败:', err)
        error.value = '加载数据失败: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // 选择饰品
    const onItemSelected = (item) => {
      selectedItem.value = item
    }

    // 饰品数据更新
    const onItemUpdated = (updatedItem) => {
      selectedItem.value = updatedItem
      // 可以选择重新加载统计数据
      fetchStats()
    }

    onMounted(() => {
      loadData()
    })

    return {
      loading,
      error,
      stats,
      chartData,
      selectedItem,
      onItemSelected,
      onItemUpdated
    }
  }
}
</script>