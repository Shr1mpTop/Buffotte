import axios from 'axios'

const client = axios.create({ baseURL: '/api', timeout: 6000 })

// 外部API客户端 - 用于调用buff-tracker服务
const externalClient = axios.create({ 
  baseURL: '/api/bufftracker',
  timeout: 10000 
})

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
  
  // 获取饰品价格
  async getItemPrice(marketHashName) {
    try {
      const { data } = await externalClient.get(`/price/${encodeURIComponent(marketHashName)}`)
      return { success: true, ...data }
    } catch (err) {
      console.error('获取价格失败:', err)
      return { success: false, error: err.response?.data || err.message }
    }
  }
}
