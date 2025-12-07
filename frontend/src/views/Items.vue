<template>
  <div class="items-page">
    <div class="items-header">
      <h1 class="title">$ ./item-search.sh</h1>
      <div class="search-box">
        <input
          v-model="searchQuery"
          @input="handleSearch"
          type="text"
          placeholder="搜索饰品名称 (支持中英文)..."
          class="search-input"
        />
        <div v-if="searching" class="search-status">搜索中...</div>
      </div>
    </div>

    <!-- 搜索结果列表 -->
    <div v-if="searchResults.length > 0" class="search-results">
      <div class="results-header">
        <span>找到 {{ searchResults.length }} 个结果</span>
      </div>
      <div class="results-list">
        <div
          v-for="item in searchResults"
          :key="item.id"
          class="result-item"
          :class="{ selected: selectedItem?.id === item.id }"
          @click="selectItem(item)"
        >
          <div class="item-name">{{ item.name }}</div>
          <div class="item-hash">{{ item.market_hash_name }}</div>
        </div>
      </div>
    </div>

    <!-- 价格详情 -->
    <div v-if="selectedItem && priceData" class="price-details">
      <div class="details-header">
        <h2>{{ selectedItem.name }}</h2>
        <span class="update-time">更新时间: {{ formatTime(priceData.updateTime) }}</span>
      </div>
      
      <div class="price-grid">
        <div
          v-for="platform in priceData.data"
          :key="platform.platform"
          class="price-card"
        >
          <div class="platform-name">{{ platform.platform }}</div>
          <div class="price-info">
            <div class="price-line">
              <span class="label">卖出价:</span>
              <span class="value price">¥{{ platform.sellPrice }}</span>
              <span class="count">({{ platform.sellCount }})</span>
            </div>
            <div class="price-line">
              <span class="label">求购价:</span>
              <span class="value price">¥{{ platform.biddingPrice }}</span>
              <span class="count">({{ platform.biddingCount }})</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loadingPrice" class="loading">
      <div class="loading-spinner"></div>
      <span>正在获取价格数据...</span>
    </div>

    <!-- 空状态 -->
    <div v-if="!searchResults.length && !searching && searchQuery" class="empty-state">
      <div class="empty-icon">🔍</div>
      <div class="empty-text">未找到匹配的饰品</div>
    </div>

    <div v-if="!searchQuery && !selectedItem" class="placeholder-state">
      <div class="placeholder-icon">💎</div>
      <div class="placeholder-text">输入饰品名称开始搜索</div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import api from '../services/api'

export default {
  name: 'Items',
  setup() {
    const searchQuery = ref('')
    const searchResults = ref([])
    const selectedItem = ref(null)
    const priceData = ref(null)
    const searching = ref(false)
    const loadingPrice = ref(false)
    let searchTimeout = null

    const handleSearch = () => {
      if (searchTimeout) clearTimeout(searchTimeout)
      
      if (!searchQuery.value.trim()) {
        searchResults.value = []
        return
      }

      searchTimeout = setTimeout(async () => {
        searching.value = true
        try {
          const result = await api.searchItems(searchQuery.value)
          if (result.success) {
            searchResults.value = result.data || []
          }
        } catch (error) {
          console.error('搜索失败:', error)
        } finally {
          searching.value = false
        }
      }, 300)
    }

    const selectItem = async (item) => {
      selectedItem.value = item
      priceData.value = null
      loadingPrice.value = true

      try {
        const result = await api.getItemPrice(item.market_hash_name)
        if (result.success) {
          priceData.value = {
            data: result.data,
            updateTime: result.data[0]?.updateTime || Date.now() / 1000
          }
        }
      } catch (error) {
        console.error('获取价格失败:', error)
      } finally {
        loadingPrice.value = false
      }
    }

    const formatTime = (timestamp) => {
      if (!timestamp) return ''
      const date = new Date(timestamp * 1000)
      return date.toLocaleString('zh-CN')
    }

    return {
      searchQuery,
      searchResults,
      selectedItem,
      priceData,
      searching,
      loadingPrice,
      handleSearch,
      selectItem,
      formatTime
    }
  }
}
</script>

<style scoped>
.items-page {
  width: 100%;
  max-width: 1200px;
  padding: 24px;
  margin: 40px auto 0;
  animation: fadeIn 0.4s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.items-header {
  margin-bottom: 32px;
}

.title {
  font-family: 'Courier New', monospace;
  font-size: 28px;
  font-weight: 700;
  color: #00ff41;
  margin: 0 0 20px 0;
  text-shadow: 0 0 10px rgba(0, 255, 65, 0.5);
}

.search-box {
  position: relative;
}

.search-input {
  width: 100%;
  padding: 14px 20px;
  font-size: 16px;
  font-family: 'Courier New', monospace;
  background: rgba(0, 0, 0, 0.6);
  border: 2px solid #00ff41;
  border-radius: 8px;
  color: #00ff41;
  outline: none;
  transition: all 0.3s ease;
}

.search-input::placeholder {
  color: rgba(0, 255, 65, 0.4);
}

.search-input:focus {
  border-color: #00ff41;
  box-shadow: 0 0 20px rgba(0, 255, 65, 0.3);
}

.search-status {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  color: #00ff41;
  font-size: 14px;
}

.search-results {
  margin-bottom: 24px;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid #00ff41;
  border-radius: 8px;
  overflow: hidden;
}

.results-header {
  padding: 12px 20px;
  background: rgba(0, 255, 65, 0.1);
  border-bottom: 1px solid #00ff41;
  color: #00ff41;
  font-family: 'Courier New', monospace;
  font-size: 14px;
}

.results-list {
  max-height: 400px;
  overflow-y: auto;
}

.result-item {
  padding: 16px 20px;
  border-bottom: 1px solid rgba(0, 255, 65, 0.2);
  cursor: pointer;
  transition: all 0.2s ease;
}

.result-item:last-child {
  border-bottom: none;
}

.result-item:hover {
  background: rgba(0, 255, 65, 0.1);
}

.result-item.selected {
  background: rgba(0, 255, 65, 0.2);
}

.item-name {
  color: #00ff41;
  font-family: 'Courier New', monospace;
  font-size: 16px;
  margin-bottom: 4px;
}

.item-hash {
  color: rgba(0, 255, 65, 0.6);
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.price-details {
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid #00ff41;
  border-radius: 8px;
  padding: 24px;
}

.details-header {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(0, 255, 65, 0.3);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.details-header h2 {
  color: #00ff41;
  font-family: 'Courier New', monospace;
  font-size: 20px;
  margin: 0;
}

.update-time {
  color: rgba(0, 255, 65, 0.6);
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.price-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.price-card {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(0, 255, 65, 0.3);
  border-radius: 8px;
  padding: 20px;
  transition: all 0.3s ease;
}

.price-card:hover {
  border-color: #00ff41;
  box-shadow: 0 0 15px rgba(0, 255, 65, 0.2);
}

.platform-name {
  color: #00ff41;
  font-family: 'Courier New', monospace;
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 16px;
  text-align: center;
}

.price-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.price-line {
  display: flex;
  align-items: center;
  gap: 8px;
}

.price-line .label {
  color: rgba(0, 255, 65, 0.7);
  font-family: 'Courier New', monospace;
  font-size: 14px;
  min-width: 70px;
}

.price-line .value.price {
  color: #00ff41;
  font-family: 'Courier New', monospace;
  font-size: 18px;
  font-weight: 700;
}

.price-line .count {
  color: rgba(0, 255, 65, 0.5);
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  gap: 16px;
  color: #00ff41;
  font-family: 'Courier New', monospace;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(0, 255, 65, 0.2);
  border-top-color: #00ff41;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.empty-state,
.placeholder-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  gap: 16px;
}

.empty-icon,
.placeholder-icon {
  font-size: 64px;
  opacity: 0.5;
}

.empty-text,
.placeholder-text {
  color: rgba(0, 255, 65, 0.6);
  font-family: 'Courier New', monospace;
  font-size: 16px;
}

/* 滚动条样式 */
.results-list::-webkit-scrollbar {
  width: 8px;
}

.results-list::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.2);
}

.results-list::-webkit-scrollbar-thumb {
  background: rgba(0, 255, 65, 0.3);
  border-radius: 4px;
}

.results-list::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 255, 65, 0.5);
}
</style>
