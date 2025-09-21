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
import '../css/SearchBox.css'

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
    const selectItem = async (item) => {
      searchQuery.value = item.name
      searchResults.value = []
      showDropdown.value = false

      try {
        // fetch full item details to ensure fields like sell_min_price exist
        const resp = await axios.get(`/api/item/${encodeURIComponent(item.id)}`)
        if (resp.data && resp.data.success && resp.data.data) {
          emit('item-selected', resp.data.data)
          return
        }
      } catch (err) {
        console.warn('fetch full item failed, fallback to list item', err)
      }

      // fallback: emit the list item if full fetch failed
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