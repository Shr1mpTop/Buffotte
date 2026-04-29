import axios from "axios";

const client = axios.create({ baseURL: "/api", timeout: 6000 });

// 外部API客户端 - 用于调用buff-tracker服务
const externalClient = axios.create({
  baseURL: "/api/bufftracker",
  timeout: 10000,
});

export { client, externalClient };

function normalizeKlineRows(rows) {
  if (!Array.isArray(rows)) return [];

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
          total_count: row[7] == null ? 0 : Number(row[7]),
        };
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
        total_count: row.total_count == null ? 0 : Number(row.total_count),
      };
    })
    .filter((row) => Number.isFinite(row.timestamp));
}

export default {
  async register(payload) {
    try {
      const { data } = await client.post("/register", payload);
      return { success: true, data };
    } catch (err) {
      let errorData = err.response?.data || err.message || "网络或服务器错误";
      // If the error is a connection refused (e.g., backend unreachable), show a friendly error
      if (
        err.message &&
        typeof err.message === "string" &&
        err.message.includes("ECONNREFUSED")
      ) {
        errorData = "无法连接到后端服务，请确认后端是否运行。";
      }
      return { success: false, error: errorData };
    }
  },
  async login(payload) {
    try {
      const { data } = await client.post("/login", payload);
      return { success: true, data };
    } catch (err) {
      let errorData = err.response?.data || err.message || "网络或服务器错误";
      if (
        err.message &&
        typeof err.message === "string" &&
        err.message.includes("ECONNREFUSED")
      ) {
        errorData = "无法连接到后端服务，请确认后端是否运行。";
      }
      return { success: false, error: errorData };
    }
  },

  // 饰品搜索
  async searchItems(name, num = 10) {
    try {
      const { data } = await externalClient.get("/search", {
        params: { name, num },
      });
      return { success: true, ...data };
    } catch (err) {
      console.error("搜索饰品失败:", err);
      return { success: false, error: err.response?.data || err.message };
    }
  },

  // 获取饰品价格（多平台实时价格）
  async getItemPrice(marketHashName) {
    try {
      const { data } = await externalClient.get(
        `/price/${encodeURIComponent(marketHashName)}`,
      );
      return { success: true, ...data };
    } catch (err) {
      console.error("获取价格失败:", err);
      return { success: false, error: err.response?.data || err.message };
    }
  },

  // 获取饰品历史价格数据（用于K线图）
  async getItemPriceHistory(itemId) {
    try {
      const { data } = await client.get(`/item-price/${itemId}`);
      return { success: true, data: data.data || [] };
    } catch (err) {
      console.error("获取历史价格失败:", err);
      return { success: false, error: err.response?.data || err.message };
    }
  },

  // 获取饰品历史 K 线数据
  async getItemKlineData(marketHashName, options = {}) {
    try {
      const { platform = "BUFF", type_day = "1", date_type = 3 } = options;
      const encodedName = encodeURIComponent(marketHashName);
      const { data } = await externalClient.get(
        `/item/kline-data/${encodedName}`,
        {
          params: { platform, type_day, date_type },
        },
      );
      // 后端返回格式: {success: true, data: [...]}
      return { success: true, data: normalizeKlineRows(data.data || []) };
    } catch (err) {
      console.error(`获取饰品 ${marketHashName} 的 K线数据失败:`, err);
      // 返回包含状态码的错误信息
      const error = {
        message: err.response?.data?.detail || err.message,
        status: err.response?.status,
      };
      return { success: false, error };
    }
  },

  // 从数据库读取缓存的K线数据（毫秒级响应）
  async getCachedItemKlineData(marketHashName) {
    try {
      const encodedName = encodeURIComponent(marketHashName);
      const { data } = await client.get(
        `/item/kline-cached/${encodedName}`
      );
      return {
        success: true,
        data: normalizeKlineRows(data.data || []),
        source: data.source,
        last_updated: data.last_updated,
      };
    } catch (err) {
      console.error(`读取缓存K线数据失败 ${marketHashName}:`, err);
      return { success: false, error: { message: err.response?.data?.detail || err.message } };
    }
  },

  // 刷新K线数据：从外部API获取最新数据并存入数据库
  async refreshItemKlineData(marketHashName) {
    try {
      const encodedName = encodeURIComponent(marketHashName);
      const { data } = await client.post(
        `/item/kline-refresh/${encodedName}`,
        null,
        { timeout: 45000 }
      );
      return {
        success: true,
        data: normalizeKlineRows(data.data || []),
        source: data.source,
        last_updated: data.last_updated,
      };
    } catch (err) {
      console.error(`刷新K线数据失败 ${marketHashName}:`, err);
      return { success: false, error: { message: err.response?.data?.detail || err.message } };
    }
  },

  // ─── Skin 智能追踪 API ───────────────────────────────────────────

  // 获取热门饰品列表
  async getTrendingSkins(limit = 20) {
    try {
      const { data } = await client.get("/skin/trending", {
        params: { limit },
      });
      return { success: true, ...data };
    } catch (err) {
      console.error("获取热门饰品失败:", err);
      return {
        success: false,
        error: err.response?.data?.detail || err.message,
      };
    }
  },

  // 搜索饰品
  async searchSkins(q, limit = 20) {
    try {
      const { data } = await client.get("/skin/search", {
        params: { q, limit },
      });
      return { success: true, ...data };
    } catch (err) {
      console.error("搜索饰品失败:", err);
      return {
        success: false,
        error: err.response?.data?.detail || err.message,
      };
    }
  },

  // 获取单个饰品详情
  async getSkinDetail(skinId) {
    try {
      const { data } = await client.get(`/skin/${skinId}/detail`);
      return { success: true, ...data };
    } catch (err) {
      console.error("获取饰品详情失败:", err);
      return {
        success: false,
        error: err.response?.data?.detail || err.message,
      };
    }
  },

  // ─── 搬砖收益计算 API ─────────────────────────────────────────────

  // 获取所有平台费率
  async getPlatformFees() {
    try {
      const { data } = await client.get("/profit/platform-fees");
      return { success: true, data: data.data || [] };
    } catch (err) {
      console.error("获取平台费率失败:", err);
      return { success: false, error: err.response?.data?.detail || err.message };
    }
  },

  // 计算单次搬砖利润
  async calculateProfit(buyPrice, sellPrice, sellPlatform = "BUFF", holdDays = 7) {
    try {
      const { data } = await client.get("/profit/calculate", {
        params: { buy_price: buyPrice, sell_price: sellPrice, sell_platform: sellPlatform, hold_days: holdDays },
      });
      return { success: true, data: data.data };
    } catch (err) {
      console.error("利润计算失败:", err);
      return { success: false, error: err.response?.data?.detail || err.message };
    }
  },

  // 预测饰品 7 天后价格 + 各平台利润
  async predictItemProfit(marketHashName) {
    try {
      const encodedName = encodeURIComponent(marketHashName);
      const { data } = await client.get(`/profit/predict/${encodedName}`, { timeout: 30000 });
      return { success: true, data: data.data };
    } catch (err) {
      console.error("预测利润失败:", err);
      return { success: false, error: err.response?.data?.detail || err.message };
    }
  },

  // 获取用户所有追踪饰品的预测利润
  async getTrackedItemsProfit(email) {
    try {
      const { data } = await client.get(`/profit/tracked/${encodeURIComponent(email)}`, { timeout: 60000 });
      return { success: true, data: data.data || [] };
    } catch (err) {
      console.error("获取追踪利润失败:", err);
      return { success: false, error: err.response?.data?.detail || err.message };
    }
  },

  // ─── 买卖笔记 API ─────────────────────────────────────────────────

  async getTradeNotePositions(email) {
    try {
      const { data } = await client.get(`/trade-notes/${encodeURIComponent(email)}/positions`);
      return { success: true, data: data.data || [] };
    } catch (err) {
      console.error("获取买卖笔记仓位失败:", err);
      return { success: false, error: err.response?.data?.detail || err.message };
    }
  },

  async getTradeNoteEntries(email, marketHashName = null) {
    try {
      const { data } = await client.get(`/trade-notes/${encodeURIComponent(email)}/entries`, {
        params: marketHashName ? { market_hash_name: marketHashName } : {},
      });
      return { success: true, data: data.data || [] };
    } catch (err) {
      console.error("获取买卖笔记流水失败:", err);
      return { success: false, error: err.response?.data?.detail || err.message };
    }
  },

  async addTradeNoteEntry(payload) {
    try {
      const { data } = await client.post("/trade-notes", payload);
      return { success: true, data: data.data };
    } catch (err) {
      console.error("新增买卖笔记失败:", err);
      return { success: false, error: err.response?.data?.detail || err.message };
    }
  },

  async deleteTradeNoteEntry(email, entryId) {
    try {
      await client.delete(`/trade-notes/${encodeURIComponent(email)}/entries/${entryId}`);
      return { success: true };
    } catch (err) {
      console.error("删除买卖笔记失败:", err);
      return { success: false, error: err.response?.data?.detail || err.message };
    }
  },
};
