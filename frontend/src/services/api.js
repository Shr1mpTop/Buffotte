import axios from 'axios'

const client = axios.create({ baseURL: '/api', timeout: 6000 })

// 外部API客户端 - 用于调用buff-tracker服务
const externalClient = axios.create({ 
  baseURL: '/api/bufftracker',
  timeout: 10000 
})

export { client, externalClient }

function normalizeKlineRows(rows) {
  if (!Array.isArray(rows)) return []

  return rows
    .map((row) => {
      // 兼容后端返回数组格式:
      // [timestamp, price, sell_count, buy_price, buy_count, turnover, volume, total_count]
      if (Array.isArray(row)) {
        return {
          timestamp: Number(row[0]),
          price: Number(row[1]),
          sell_count: Number(row[2]),
          buy_price: Number(row[3]),
          buy_count: Number(row[4]),
          turnover: row[5] == null ? 0 : Number(row[5]),
          volume: row[6] == null ? 0 : Number(row[6]),
          total_count: row[7] == null ? 0 : Number(row[7])
        }
      }

      // 兼容后端已格式化对象
      return {
        timestamp: Number(row.timestamp),
        price: Number(row.price),
        sell_count: Number(row.sell_count),
        buy_price: Number(row.buy_price),
        buy_count: Number(row.buy_count),
        turnover: row.turnover == null ? 0 : Number(row.turnover),
        volume: row.volume == null ? 0 : Number(row.volume),
        total_count: row.total_count == null ? 0 : Number(row.total_count)
      }
    })
    .filter((row) => Number.isFinite(row.timestamp))
}

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
  async getItemKlineData(marketHashName, options = {}) {
    try {
      const { platform = 'BUFF', type_day = '1', date_type = 3 } = options
      const encodedName = encodeURIComponent(marketHashName)
      const { data } = await externalClient.get(`/item/kline-data/${encodedName}`, {
        params: { platform, type_day, date_type }
      })
      // 后端返回格式: {success: true, data: [...]}
      return { success: true, data: normalizeKlineRows(data.data || []) }
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
