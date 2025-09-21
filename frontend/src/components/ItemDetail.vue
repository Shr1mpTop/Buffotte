<template>
  <div v-if="item" class="item-detail-card">
    <div class="card-header">
      <h3 class="item-title">{{ item.name }}</h3>
      <div class="update-time">
        更新时间: {{ formatTime(item.updated_at) }}
      </div>
    </div>
    
    <div class="price-grid">
      <div class="price-item buy-price">
        <div class="price-label">💰 最高收购价</div>
        <div class="price-value">¥{{ item.buy_max_price || '0.00' }}</div>
        <div class="price-count">{{ item.buy_num || 0 }} 个求购</div>
      </div>
      
      <div class="price-item sell-price">
        <div class="price-label">🏷️ 最低售价</div>
        <div class="price-value">¥{{ item.sell_min_price || '0.00' }}</div>
        <div class="price-count">{{ item.sell_num || 0 }} 个在售</div>
      </div>
      
      <div class="price-item reference-price">
        <div class="price-label">📊 参考价格</div>
        <div class="price-value">¥{{ item.sell_reference_price || '0.00' }}</div>
        <div class="price-count">{{ item.transacted_num || 0 }} 个成交</div>
      </div>
    </div>
    
    <div class="item-actions">
      <button @click="refreshItem" :disabled="refreshing" class="refresh-btn" :class="{ 'refreshing': refreshing }">
        <span v-if="!refreshing" class="refresh-icon">🔄</span>
        <span v-else class="loading-spinner">⏳</span>
        {{ refreshing ? '刷新中...' : '刷新数据' }}
      </button>
      <a 
        v-if="item.steam_market_url" 
        :href="item.steam_market_url" 
        target="_blank" 
        class="steam-link"
      >
        🎮 Steam市场
      </a>
    </div>
    
    <!-- 刷新结果提示 -->
    <div v-if="refreshMessage" class="refresh-message" :class="refreshMessageType">
      {{ refreshMessage }}
    </div>
    
    <!-- 价格变化提示 -->
    <div v-if="priceChange" class="price-change" :class="priceChange.diff > 0 ? 'price-up' : 'price-down'">
      价格变化: {{ priceChange.diff > 0 ? '+' : '' }}¥{{ Math.abs(priceChange.diff).toFixed(2) }}
      <div class="price-change-detail">
        {{ priceChange.before }} → {{ priceChange.after }}
      </div>
    </div>
    <!-- 价格历史图（非等距时间轴） -->
    <div class="price-history-section" v-if="historySeries && historySeries.length">
      <h4>历史价格走势</h4>
      <PriceHistoryChart :series="historySeries" />
    </div>

    <div class="price-history-loading" v-else-if="historyLoading">
      加载历史价格中...
    </div>

    <div class="price-history-empty" v-else>
      <p>暂无历史价格数据。</p>
    </div>
  </div>
  
  <div v-else class="no-item">
    <div class="no-item-icon">🔍</div>
    <div class="no-item-text">请搜索并选择一个饰品</div>
  </div>
</template>

<script>
import { ref, watch, onMounted } from 'vue'
import axios from 'axios'
import '../css/ItemDetail.css'
import PriceHistoryChart from './PriceHistoryChart.vue'

export default {
  name: 'ItemDetail',
  props: {
    item: {
      type: Object,
      default: null
    }
  },
  emits: ['item-updated'],
  components: {
    PriceHistoryChart
  },
  setup(props, { emit }) {
    const refreshing = ref(false)
    const refreshMessage = ref('')
    const refreshMessageType = ref('') // 'success', 'warning', 'error'
    const priceChange = ref(null)
  const historySeries = ref([])
  const historyLoading = ref(false)

    // 刷新饰品数据
    const refreshItem = async () => {
      if (!props.item || refreshing.value) return

      refreshing.value = true
      refreshMessage.value = ''
      priceChange.value = null
      
      console.log(`开始刷新物品数据: ID=${props.item.id}, Name=${props.item.name}`)
      
      try {
        const response = await axios.post('/api/refresh-item', {
          id: props.item.id,
          name: props.item.name
        })
        
        const result = response.data
        
        if (result.success) {
          // 更新数据
          emit('item-updated', result.data)
          
          // 显示刷新结果
          refreshMessage.value = result.message
          refreshMessageType.value = result.priceChanged ? 'success' : 'warning'
          
          // 显示价格变化
          if (result.priceChange) {
            priceChange.value = result.priceChange
          }
          
          console.log('刷新成功:', result.message)
        } else {
          refreshMessage.value = result.message || '刷新失败'
          refreshMessageType.value = 'error'
          console.error('刷新失败:', result)
        }
      } catch (error) {
        console.error('刷新饰品数据失败:', error)
        refreshMessage.value = error.response?.data?.message || '网络请求失败'
        refreshMessageType.value = 'error'
      } finally {
        refreshing.value = false
        
        // 3秒后清除消息
        setTimeout(() => {
          refreshMessage.value = ''
          priceChange.value = null
        }, 5000)
      }
    }

    // 加载价格历史
    const loadHistory = async () => {
      if (!props.item) return
      historyLoading.value = true
      historySeries.value = []
      try {
        const id = props.item.id
        const resp = await axios.get(`/api/item/${encodeURIComponent(id)}/history`)
        if (resp.data && resp.data.success && Array.isArray(resp.data.data)) {
          historySeries.value = resp.data.data.map(r => ({ time: r.recorded_at, price: parseFloat(r.sell_min_price) }))
        } else {
          // backend returned no data or unsuccessful
          historySeries.value = []
        }
      } catch (e) {
        console.error('加载历史价格失败', e)
        historySeries.value = []
      } finally {
        historyLoading.value = false
      }
    }
      
    // 监听 item 变化，加载历史
    watch(() => props.item, (v) => {
      if (v) loadHistory()
      else {
        historySeries.value = []
      }
    }, { immediate: true })

    // 格式化时间
    const formatTime = (timeString) => {
      if (!timeString) return '未知'
      const date = new Date(timeString)
      return date.toLocaleString('zh-CN')
    }

    return {
      refreshing,
      refreshMessage,
      refreshMessageType,
      priceChange,
      refreshItem,
      formatTime
      , historySeries, historyLoading, loadHistory
    }
  }
}
</script>