<template>
  <div class="search-container">
    <div class="search-box">
      <input
        v-model="searchQuery"
        @input="onSearch"
        @focus="showDropdown = true"
        @blur="hideDropdown"
        type="text"
        placeholder="搜索饰品名称..."
        class="search-input"
      />
      <div class="search-icon">🔍</div>
    </div>
    
    <!-- 搜索结果下拉框 -->
    <div v-if="showDropdown && searchResults.length > 0" class="search-dropdown">
      <div
        v-for="item in searchResults"
        :key="item.id"
        @mousedown="selectItem(item)"
        class="search-item"
      >
        <div class="item-name">{{ item.name }}</div>
        <div class="item-price">¥{{ item.sell_min_price }}</div>
      </div>
    </div>
    
    <!-- 加载状态 -->
    <div v-if="searching" class="search-loading">
      正在搜索...
    </div>
  </div>
</template>

<script>
import { ref, watch } from 'vue'
import axios from 'axios'

export default {
  name: 'SearchBox',
  emits: ['item-selected'],
  setup(props, { emit }) {
    const searchQuery = ref('')
    const searchResults = ref([])
    const showDropdown = ref(false)
    const searching = ref(false)
    let searchTimeout = null

    // 防抖搜索
    const onSearch = () => {
      if (searchTimeout) {
        clearTimeout(searchTimeout)
      }
      
      if (searchQuery.value.trim().length < 2) {
        searchResults.value = []
        showDropdown.value = false
        return
      }

      searchTimeout = setTimeout(async () => {
        await performSearch()
      }, 300)
    }

    // 执行搜索
    const performSearch = async () => {
      if (!searchQuery.value.trim()) return

      searching.value = true
      try {
        const response = await axios.get('/api/search', {
          params: { q: searchQuery.value.trim() }
        })
        
        if (response.data.success) {
          searchResults.value = response.data.data
          showDropdown.value = true
        }
      } catch (error) {
        console.error('搜索失败:', error)
        searchResults.value = []
      } finally {
        searching.value = false
      }
    }

    // 选择搜索项
    const selectItem = (item) => {
      searchQuery.value = item.name
      searchResults.value = []
      showDropdown.value = false
      emit('item-selected', item)
    }

    // 隐藏下拉框（延迟隐藏以允许点击）
    const hideDropdown = () => {
      setTimeout(() => {
        showDropdown.value = false
      }, 200)
    }

    return {
      searchQuery,
      searchResults,
      showDropdown,
      searching,
      onSearch,
      selectItem,
      hideDropdown
    }
  }
}
</script>

<style scoped>
.search-container {
  position: relative;
  width: 100%;
  max-width: 400px;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-input {
  width: 100%;
  padding: 12px 45px 12px 15px;
  border: 2px solid #e1e5e9;
  border-radius: 25px;
  font-size: 16px;
  outline: none;
  transition: all 0.3s ease;
  background: white;
}

.search-input:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.search-icon {
  position: absolute;
  right: 15px;
  color: #666;
  pointer-events: none;
}

.search-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e1e5e9;
  border-radius: 10px;
  box-shadow: 0 5px 20px rgba(0,0,0,0.1);
  max-height: 300px;
  overflow-y: auto;
  z-index: 1000;
  margin-top: 5px;
}

.search-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 15px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s;
}

.search-item:hover {
  background-color: #f8f9fa;
}

.search-item:last-child {
  border-bottom: none;
}

.item-name {
  font-weight: 500;
  color: #333;
  flex: 1;
  margin-right: 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-price {
  font-weight: bold;
  color: #667eea;
  font-size: 14px;
}

.search-loading {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e1e5e9;
  border-radius: 10px;
  padding: 15px;
  text-align: center;
  color: #666;
  margin-top: 5px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}
</style>