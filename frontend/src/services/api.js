import axios from 'axios'

const client = axios.create({ baseURL: '/api', timeout: 6000 })

// 外部API客户端 - 用于调用buff-tracker服务
const externalClient = axios.create({ 
  baseURL: '/api/bufftracker',
  timeout: 10000 
})

export { client, externalClient }

export default {
  async register(payload) {
    try {
      const { data } = await client.post('/register', payload)
      return { success: true, data }
    } catch (err) {
      let errorData = err.response?.data || err.message || '网络或服务器错误'
      // If the error is a connection refused (e.g., backend unreachable), show a friendly error
      if (err.message && typeof err.message === 'string' && err.message.includes('ECONNREFUSED')) {
        errorData = '无法连接到后端服务，请确认后端是否运行。'
      }
      return { success: false, error: errorData }
    }
  },
  async login(payload) {
    try {
      const { data } = await client.post('/login', payload)
      return { success: true, data }
    } catch (err) {
      let errorData = err.response?.data || err.message || '网络或服务器错误'
      if (err.message && typeof err.message === 'string' && err.message.includes('ECONNREFUSED')) {
        errorData = '无法连接到后端服务，请确认后端是否运行。'
      }
      return { success: false, error: errorData }
    }
  },
  
  // 饰品搜索
  async searchItems(name, num = 10) {
    try {
      const { data } = await externalClient.get('/search', {
        params: { name, num }
      })
      return { success: true, ...data }
    } catch (err) {
      console.error('搜索饰品失败:', err)
      return { success: false, error: err.response?.data || err.message }
    }
  },
  
  // 获取饰品价格（多平台实时价格）
  async getItemPrice(marketHashName) {
    try {
      const { data } = await externalClient.get(`/price/${encodeURIComponent(marketHashName)}`)
      return { success: true, ...data }
    } catch (err) {
      console.error('获取价格失败:', err)
      return { success: false, error: err.response?.data || err.message }
    }
  },

  // 获取饰品历史价格数据（用于K线图）
  async getItemPriceHistory(itemId) {
    try {
      const { data } = await client.get(`/item-price/${itemId}`)
      return { success: true, data: data.data || [] }
    } catch (err) {
      console.error('获取历史价格失败:', err)
      return { success: false, error: err.response?.data || err.message }
    }
  },

  // 获取饰品历史 K 线数据
  async getItemKlineData(marketHashName) {
    try {
      const { data } = await client.get(`/item/kline-data/${marketHashName}`)
      // 后端返回格式: {success: true, data: [...]}
      return { success: true, data: data.data || [] }
    } catch (err) {
      console.error(`获取饰品 ${marketHashName} 的 K线数据失败:`, err)
      // 返回包含状态码的错误信息
      const error = {
        message: err.response?.data?.detail || err.message,
        status: err.response?.status
      }
      return { success: false, error }
    }
  }
}
