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
      <button @click="refreshItem" :disabled="refreshing" class="refresh-btn">
        {{ refreshing ? '刷新中...' : '🔄 刷新数据' }}
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
  </div>
  
  <div v-else class="no-item">
    <div class="no-item-icon">🔍</div>
    <div class="no-item-text">请搜索并选择一个饰品</div>
  </div>
</template>

<script>
import { ref } from 'vue'
import axios from 'axios'

export default {
  name: 'ItemDetail',
  props: {
    item: {
      type: Object,
      default: null
    }
  },
  emits: ['item-updated'],
  setup(props, { emit }) {
    const refreshing = ref(false)

    // 刷新饰品数据
    const refreshItem = async () => {
      if (!props.item || refreshing.value) return

      refreshing.value = true
      try {
        const response = await axios.post('/api/refresh-item', {
          id: props.item.id,
          name: props.item.name
        })
        
        if (response.data.success) {
          emit('item-updated', response.data.data)
        } else {
          throw new Error(response.data.message || '刷新失败')
        }
      } catch (error) {
        console.error('刷新饰品数据失败:', error)
        alert('刷新失败: ' + error.message)
      } finally {
        refreshing.value = false
      }
    }

    // 格式化时间
    const formatTime = (timeString) => {
      if (!timeString) return '未知'
      const date = new Date(timeString)
      return date.toLocaleString('zh-CN')
    }

    return {
      refreshing,
      refreshItem,
      formatTime
    }
  }
}
</script>

<style scoped>
.item-detail-card {
  background: white;
  padding: 25px;
  border-radius: 15px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.1);
  margin-top: 20px;
}

.card-header {
  margin-bottom: 20px;
  text-align: center;
}

.item-title {
  font-size: 1.5rem;
  font-weight: bold;
  color: #333;
  margin-bottom: 8px;
  word-break: break-word;
}

.update-time {
  color: #666;
  font-size: 0.9rem;
}

.price-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin-bottom: 25px;
}

.price-item {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 12px;
  text-align: center;
  border-left: 4px solid;
}

.buy-price {
  border-left-color: #28a745;
}

.sell-price {
  border-left-color: #dc3545;
}

.reference-price {
  border-left-color: #667eea;
}

.price-label {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 8px;
}

.price-value {
  font-size: 1.5rem;
  font-weight: bold;
  color: #333;
  margin-bottom: 5px;
}

.price-count {
  font-size: 0.8rem;
  color: #888;
}

.item-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
  align-items: center;
}

.refresh-btn {
  padding: 10px 20px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s ease;
}

.refresh-btn:hover:not(:disabled) {
  background: #5a6fd8;
  transform: translateY(-1px);
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.steam-link {
  padding: 10px 20px;
  background: #1b2838;
  color: white;
  text-decoration: none;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s ease;
}

.steam-link:hover {
  background: #2a475e;
  transform: translateY(-1px);
}

.no-item {
  background: white;
  padding: 50px 25px;
  border-radius: 15px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.1);
  text-align: center;
  margin-top: 20px;
}

.no-item-icon {
  font-size: 3rem;
  margin-bottom: 15px;
  opacity: 0.5;
}

.no-item-text {
  color: #666;
  font-size: 1.1rem;
}

@media (max-width: 768px) {
  .price-grid {
    grid-template-columns: 1fr;
  }
  
  .item-actions {
    flex-direction: column;
  }
  
  .refresh-btn,
  .steam-link {
    width: 100%;
    text-align: center;
  }
}
</style>