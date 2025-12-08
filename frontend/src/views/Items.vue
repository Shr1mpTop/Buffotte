<template>
  <div class="items-page">
    <div class="items-grid-container">
      <!-- 搜索器 -->
      <div class="search-panel">
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

      <!-- 实时价格看板 -->
      <div class="price-panel">
        <div v-if="selectedItem && priceData" class="price-details">
          <div class="details-header">
            <h2>{{ selectedItem.name }}</h2>
            <span class="update-time">更新时间: {{ formatTime(priceData.updateTime) }}</span>
          </div>
          
          <div class="price-grid">
            <template v-for="(platform, index) in Array(10).fill(null).map((_, i) => priceData.data[i] || { platform: '-', sellPrice: '-', sellCount: '-', biddingPrice: '-', biddingCount: '-' })" :key="index">
              <div
                class="price-card"
                :class="{ 'empty-card': platform.platform === '-' }"
              >
                <div class="platform-name">{{ platform.platform }}</div>
                <div class="price-info">
                  <div class="price-line">
                    <span class="label">卖出价:</span>
                    <span
                      class="value price"
                      :class="{ 'highest-sell': platform.sellPrice === highestSellPrice && highestSellPrice !== null }"
                    >¥{{ platform.sellPrice }}</span>
                    <span class="count">({{ platform.sellCount }})</span>
                  </div>
                  <div class="price-line">
                    <span class="label">求购价:</span>
                    <span
                      class="value price"
                      :class="{ 'lowest-bidding': platform.biddingPrice === lowestBiddingPrice && lowestBiddingPrice !== null }"
                    >¥{{ platform.biddingPrice }}</span>
                    <span class="count">({{ platform.biddingCount }})</span>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- 加载状态 -->
        <div v-if="loadingPrice" class="loading">
          <div class="loading-spinner"></div>
          <span>正在获取价格数据...</span>
        </div>
      </div>

      <!-- K线看板 -->
      <div class="kline-panel">
        <div v-if="klineData.length > 0" ref="klineChart" class="kline-chart-container"></div>
        <div v-if="loadingKlineData" class="loading">
          <div class="loading-spinner"></div>
          <span>正在获取K线数据...</span>
        </div>
        <div v-else-if="klineError" class="error-state">
          <div class="error-icon">⚠️</div>
          <div class="error-text">{{ klineError }}</div>
        </div>
        <div v-else-if="!loadingKlineData && !klineData.length && selectedItem" class="empty-state">
          <div class="empty-icon">📈</div>
          <div class="empty-text">暂无K线数据</div>
        </div>
        <div v-else-if="!selectedItem" class="placeholder-state">
          <div class="placeholder-icon">📊</div>
          <div class="placeholder-text">选择饰品查看K线图</div>
        </div>
      </div>

      <!-- 数据图表板块 (存世量、买卖差额等) -->
      <div class="data-panel">
        <div v-if="klineData.length > 0" ref="dataChart" class="data-chart-container"></div>
        <div v-if="loadingKlineData" class="loading">
          <div class="loading-spinner"></div>
          <span>正在加载数据...</span>
        </div>
        <div v-else-if="klineError" class="error-state">
          <div class="error-icon">⚠️</div>
          <div class="error-text">{{ klineError }}</div>
        </div>
        <div v-else-if="!loadingKlineData && !klineData.length && selectedItem" class="empty-state">
          <div class="empty-icon">📉</div>
          <div class="empty-text">暂无数据</div>
        </div>
        <div v-else-if="!selectedItem" class="placeholder-state">
          <div class="placeholder-icon">📊</div>
          <div class="placeholder-text">选择饰品查看数据图表</div>
        </div>
      </div>

      <!-- 数据图表板块 (存世量、买卖差额等) -->
      <div class="data-panel">
        <div v-if="klineData.length > 0" ref="dataChart" class="data-chart-container"></div>
        <div v-if="loadingKlineData" class="loading">
          <div class="loading-spinner"></div>
          <span>正在加载数据...</span>
        </div>
        <div v-else-if="klineError" class="error-state">
          <div class="error-icon">⚠️</div>
          <div class="error-text">{{ klineError }}</div>
        </div>
        <div v-else-if="!loadingKlineData && !klineData.length && selectedItem" class="empty-state">
          <div class="empty-icon">📉</div>
          <div class="empty-text">暂无数据</div>
        </div>
        <div v-else-if="!selectedItem" class="placeholder-state">
          <div class="placeholder-icon">📊</div>
          <div class="placeholder-text">选择饰品查看数据图表</div>
        </div>
      </div>

      <!-- 追踪按钮 -->
      <div class="tracking-panel">
        <button
          class="track-button"
          @click="trackItem(selectedItem.market_hash_name)"
          :disabled="!selectedItem"
        >
          ⭐ 追踪此饰品
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, shallowRef, onMounted, watch, nextTick } from 'vue'
import api, { client } from '../services/api'
import * as echarts from 'echarts/core'
import { useToast } from '../composables/useToast'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  MarkPointComponent,
  MarkLineComponent
} from 'echarts/components'
import { CandlestickChart, LineChart, BarChart } from 'echarts/charts'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  MarkPointComponent,
  MarkLineComponent,
  CandlestickChart,
  LineChart,
  BarChart,
  CanvasRenderer
])

export default {
  name: 'Items',
  setup() {
    const searchQuery = ref('')
    const searchResults = ref([])
    const selectedItem = ref(null)
    const priceData = ref(null)
    const searching = ref(false)
    const loadingPrice = ref(false)
    const klineData = ref([])
    const loadingKlineData = ref(false)
    const klineError = ref(null) // 用于跟踪K线数据获取错误
    const klineChart = ref(null) // 用于ECharts容器的引用
    const myKlineChart = shallowRef(null) // 用于ECharts实例的引用
    const dataChart = ref(null) // 用于数据图表容器的引用
    const myDataChart = shallowRef(null) // 用于数据图表实例的引用
    const highestSellPrice = ref(null) // 用于最高售卖价
    const lowestBiddingPrice = ref(null) // 用于最低求购价
    const user = ref(JSON.parse(localStorage.getItem('user')))
    let searchTimeout = null
    const toast = useToast()

    const trackItem = async (marketHashName) => {
      if (!user.value) {
        toast.error('请先登录再追踪饰品。')
        return
      }
      try {
        const result = await client.post('/track/add', {
          email: user.value.email,
          market_hash_name: marketHashName
        })
        if (result.data.success) {
          toast.success('饰品已成功追踪！')
        } else {
          toast.error(`追踪失败: ${result.data.message}`)
        }
      } catch (error) {
        console.error('追踪饰品时出错:', error)
        toast.error('追踪饰品时出错，请查看控制台获取更多信息。')
      }
    }


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
      klineData.value = []
      klineError.value = null
      loadingPrice.value = true
      loadingKlineData.value = true
      highestSellPrice.value = null // 重置最高售卖价
      lowestBiddingPrice.value = null // 重置最低求购价

      try {
        // 获取实时价格数据
        const priceResult = await api.getItemPrice(item.market_hash_name)
        if (priceResult.success) {
          priceData.value = {
            data: priceResult.data,
            updateTime: priceResult.data[0]?.updateTime || Date.now() / 1000
          }

          // 计算最高售卖价和最低求购价
          let maxSell = 0
          let minBidding = Infinity
          priceResult.data.forEach(p => {
            // 排除Steam平台和价格为0的数据
            if (p.platform === 'Steam' || p.sellPrice === 0 || p.biddingPrice === 0) {
              return
            }
            if (p.sellPrice > maxSell) maxSell = p.sellPrice
            if (p.biddingPrice < minBidding) minBidding = p.biddingPrice
          })
          highestSellPrice.value = maxSell > 0 ? maxSell : null
          lowestBiddingPrice.value = minBidding !== Infinity ? minBidding : null
          console.log('Calculated highestSellPrice:', highestSellPrice.value)
          console.log('Calculated lowestBiddingPrice:', lowestBiddingPrice.value)

        }
      } catch (error) {
        console.error('获取价格失败:', error)
      } finally {
        loadingPrice.value = false
      }

      try {
        // 获取K线数据
        const klineResult = await api.getItemKlineData(item.market_hash_name)
        console.log('K线数据返回:', klineResult)
        if (klineResult.success) {
          klineData.value = klineResult.data || []
          console.log('K线数据长度:', klineData.value.length)
          console.log('K线数据示例:', klineData.value[0])
          klineError.value = null
        } else {
          // 处理API返回的错误
          if (klineResult.error?.status === 404) {
            klineError.value = '该饰品暂不支持K线查询,请尝试其他饰品'
          } else {
            klineError.value = klineResult.error?.message || '获取K线数据失败,请稍后重试'
          }
        }
      } catch (error) {
        console.error('获取K线数据失败:', error)
        klineError.value = '获取K线数据失败,请稍后重试'
      } finally {
        loadingKlineData.value = false
      }
    }

    const formatTime = (timestamp) => {
      if (!timestamp) return ''
      const date = new Date(timestamp * 1000)
      return date.toLocaleString('zh-CN')
    }

    // ECharts K线图配置项
    const upColor = '#00ff00'
    const downColor = '#ff0000'

    const klineOption = {
      backgroundColor: '#000',
      title: {
        text: 'K-Line Chart',
        left: 'center',
        textStyle: { color: '#00ff00', fontSize: 16 }
      },
      legend: {
        data: ['Daily Price', 'Buy Price', '交易个数'],
        top: '8%',
        textStyle: { color: '#ccc', fontSize: 12 },
        inactiveColor: '#555'
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        borderColor: '#00ff00',
        textStyle: { color: '#00ff00' },
        formatter: function (params) {
          if (!params || params.length === 0) return ''
          let res = `日期: ${params[0].name}<br/>`
          
          params.forEach(param => {
            if (param.seriesName === 'Daily Price' && param.data !== undefined) {
              res += `在售最低价: ${param.data.toFixed(2)}<br/>`
            } else if (param.seriesName === 'Buy Price' && param.data !== undefined) {
              res += `求购最高价: ${param.data.toFixed(2)}<br/>`
            } else if (param.seriesName === '交易个数' && param.data !== undefined) {
              res += `交易个数: ${param.data}<br/>`
            }
          })
          return res
        }
      },
      grid: { left: '10%', right: '10%', bottom: '12%', top: '18%', height: '68%' }, // 调整高度
      xAxis: {
        type: 'category',
        scale: true,
        boundaryGap: false,
        axisLine: { onZero: false, lineStyle: { color: '#8392A5' } },
        splitLine: { show: false },
        min: 'dataMin',
        max: 'dataMax',
        axisLabel: {
          formatter: (value) => {
            const date = new Date(value)
            return `${date.getMonth() + 1}/${date.getDate()}` // 只显示月/日
          }
        }
      },
      yAxis: {
        scale: true,
        position: 'left',
        axisLine: { lineStyle: { color: '#00ff00' } },
        splitLine: { show: true, lineStyle: { color: 'rgba(0, 255, 65, 0.1)' } },
        axisLabel: { color: '#00ff00' }
      },
      dataZoom: [
        { type: 'inside', start: 70, end: 100 },
        {
          show: true,
          type: 'slider',
          top: '90%',
          start: 70,
          end: 100,
          handleIcon: 'path://M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z M13.3,24.4H6.7V23h6.6V24.4z M13.3,19.6H6.7v-1.4h6.6V19.6z',
          handleSize: '80%',
          handleStyle: {
            color: '#fff',
            shadowBlur: 3,
            shadowColor: 'rgba(0, 0, 0, 0.6)',
            shadowOffsetX: 2,
            shadowOffsetY: 2
          }
        }
      ],
      series: [] // 系列将动态生成
    }

    // 数据处理函数
    function splitData(rawData) {
      console.log('splitData 接收到的数据:', rawData)
      let categoryData = [] // X轴日期
      let candlestickData = [] // K线图数据: [open, close, low, high]
      let totalCountData = [] // 存世量数据
      let buyCountData = [] // 求购数量数据
      let sellCountData = [] // 在售数量数据
      let turnoverData = [] // 交易额数据
      let volumeData = [] // 交易个数数据
      
      if (!rawData || rawData.length === 0) {
        console.warn('splitData: 数据为空')
        return { categoryData, candlestickData, totalCountData, buyCountData, sellCountData, turnoverData, volumeData }
      }
      
      for (let i = 0; i < rawData.length; i++) {
        const item = rawData[i]
        if (!item) continue
        
        // 数据格式验证
        if (item.timestamp === undefined || item.price === undefined || item.buy_price === undefined || item.total_count === undefined || item.sell_count === undefined || item.buy_count === undefined || item.turnover === undefined || item.volume === undefined) {
          console.warn('数据格式错误:', item)
          continue
        }

        const price = parseFloat(item.price)
        const buyPrice = parseFloat(item.buy_price)
        const totalCount = parseInt(item.total_count)
        const sellCount = parseInt(item.sell_count)
        const buyCount = parseInt(item.buy_count)
        const turnover = parseFloat(item.turnover)
        const volume = parseInt(item.volume)

        const open = buyPrice
        const close = price
        const low = Math.min(price, buyPrice)
        const high = Math.max(price, buyPrice)

        categoryData.push(new Date(item.timestamp * 1000).toLocaleDateString('zh-CN'))
        candlestickData.push([open, close, low, high])
        totalCountData.push(totalCount)
        buyCountData.push(buyCount)
        sellCountData.push(sellCount)
        turnoverData.push(turnover)
        volumeData.push(volume)
      }
      
      console.log('splitData 处理后:', { categoryData, candlestickData, totalCountData, buyCountData, sellCountData, turnoverData, volumeData })
      return { categoryData, candlestickData, totalCountData, buyCountData, sellCountData, turnoverData, volumeData }
    }

    // 计算移动平均线
    function calculateMA(dayCount, values) {
      let result = []
      for (let i = 0; i < values.length; i++) {
        if (i < dayCount - 1) {
          result.push('-')
          continue
        }
        let sum = 0
        for (let j = 0; j < dayCount; j++) {
          sum += values[i - j][1] // 使用收盘价计算均线
        }
        result.push((sum / dayCount).toFixed(2))
      }
      return result
    }

    // 初始化K线图
    const initKlineChart = async () => {
      if (!klineData.value || klineData.value.length === 0) {
        console.log('没有K线数据,跳过初始化')
        return
      }
      await nextTick() // 等待 DOM 渲染完成
      if (!klineChart.value) {
        console.error('K线图容器未找到')
        return
      }
      if (myKlineChart.value) {
        myKlineChart.value.dispose() // 清除旧实例
      }
      console.log('初始化K线图,数据条数:', klineData.value.length)
      myKlineChart.value = echarts.init(klineChart.value, 'dark')
      // 不设置空的 klineOption,直接调用 updateKlineChart
      updateKlineChart()
    }

    // 更新K线图数据
    const updateKlineChart = () => {
      if (!myKlineChart.value || !klineData.value.length) {
        myKlineChart.value?.clear()
        return
      }

      const { categoryData, candlestickData, totalCountData, buyCountData, sellCountData, turnoverData, volumeData } = splitData(klineData.value)

      myKlineChart.value.setOption({
        ...klineOption,
        xAxis: {
          ...klineOption.xAxis,
          data: categoryData
        },
        yAxis: [
          { // 第一个Y轴: 价格
            scale: true,
            position: 'left',
            axisLine: { lineStyle: { color: '#00ff00' } },
            splitLine: { show: true, lineStyle: { color: 'rgba(0, 255, 65, 0.1)' } },
            axisLabel: { color: '#00ff00' }
          },
          { // 第二个Y轴: 交易个数
            scale: true,
            position: 'right',
            alignTicks: true,
            axisLine: { lineStyle: { color: '#ADFF2F' } },
            axisLabel: { color: '#ADFF2F', fontSize: 11 }
          }
        ],
        series: [
          {
            name: 'Daily Price',
            type: 'line',
            data: candlestickData.map(item => item[1]), /* 使用收盘价 */
            smooth: true,
            showSymbol: false,
            lineStyle: { opacity: 0.8, width: 2, color: upColor }
          },
          {
            name: 'Buy Price',
            type: 'line',
            data: candlestickData.map(item => item[0]), /* 使用开盘价作为求购价 */
            smooth: true,
            showSymbol: false,
            lineStyle: { opacity: 0.8, width: 2, color: downColor }
          },
          {
            name: '交易个数',
            type: 'bar',
            data: volumeData,
            yAxisIndex: 1,
            itemStyle: { color: '#ADFF2F', opacity: 0.5 }
          }
        ]
      })
      
      // 更新数据图表
      updateDataChart(categoryData, totalCountData, buyCountData, sellCountData, turnoverData, volumeData)
    }
    
    // 初始化数据图表
    const initDataChart = async () => {
      if (!klineData.value || klineData.value.length === 0) {
        console.log('没有数据,跳过数据图表初始化')
        return
      }
      await nextTick()
      if (!dataChart.value) {
        console.error('数据图表容器未找到')
        return
      }
      if (myDataChart.value) {
        myDataChart.value.dispose()
      }
      console.log('初始化数据图表,数据条数:', klineData.value.length)
      myDataChart.value = echarts.init(dataChart.value, 'dark')
      updateDataChart()
    }
    
    // 更新数据图表
    const updateDataChart = (categoryData, totalCountData, buyCountData, sellCountData, turnoverData, volumeData) => {
      if (!myDataChart.value) return
      
      // 如果没有传入参数,则重新计算
      if (!categoryData) {
        if (!klineData.value.length) {
          myDataChart.value?.clear()
          return
        }
        const data = splitData(klineData.value)
        categoryData = data.categoryData
        totalCountData = data.totalCountData
        buyCountData = data.buyCountData
        sellCountData = data.sellCountData
        turnoverData = data.turnoverData
        volumeData = data.volumeData
      }
      
      myDataChart.value.setOption({
        backgroundColor: '#000',
        title: {
          text: '成交量分析',
          left: 'center',
          textStyle: { color: '#00ff00', fontSize: 16 }
        },
        dataZoom: [
          { type: 'inside', start: 70, end: 100 },
          {
            show: true,
            type: 'slider',
            top: '90%',
            start: 70,
            end: 100,
            handleIcon: 'path://M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z M13.3,24.4H6.7V23h6.6V24.4z M13.3,19.6H6.7v-1.4h6.6V19.6z',
            handleSize: '80%',
            handleStyle: {
              color: '#fff',
              shadowBlur: 3,
              shadowColor: 'rgba(0, 0, 0, 0.6)',
              shadowOffsetX: 2,
              shadowOffsetY: 2
            }
          }
        ],
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'cross' },
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          borderColor: '#00ff00',
          textStyle: { color: '#00ff00' }
        },
        legend: {
          data: ['存世量', '求购数量', '在售数量', '交易额'],
          top: '8%',
          textStyle: { color: '#ccc', fontSize: 12 },
          inactiveColor: '#555'
        },
        grid: { left: '10%', right: '10%', bottom: '12%', top: '18%', height: '68%' },
        xAxis: {
          type: 'category',
          data: categoryData,
          axisLine: { lineStyle: { color: '#8392A5' } },
          axisLabel: {
            formatter: (value) => {
              const date = new Date(value)
              return `${date.getMonth() + 1}/${date.getDate()}`
            }
          }
        },
        yAxis: [
          {
            type: 'value',
            name: '存世量',
            position: 'left',
            alignTicks: true,
            axisLine: { lineStyle: { color: '#8A2BE2' } },
            axisLabel: { color: '#8A2BE2', fontSize: 11 }
          },
          {
            type: 'value',
            name: '买卖数量',
            position: 'right',
            alignTicks: true,
            axisLine: { lineStyle: { color: '#00BFFF' } },
            axisLabel: { color: '#00BFFF', fontSize: 11 }
          },
          {
            type: 'value',
            name: '交易额',
            position: 'right',
            offset: 60,
            alignTicks: true,
            axisLine: { lineStyle: { color: '#FFA500' } },
            axisLabel: { color: '#FFA500', fontSize: 11 }
          }
        ],
        series: [
          {
            name: '存世量',
            type: 'line',
            data: totalCountData,
            yAxisIndex: 0,
            smooth: true,
            showSymbol: false,
            lineStyle: { color: '#8A2BE2', width: 2 }
          },
          {
            name: '求购数量',
            type: 'line',
            data: buyCountData,
            yAxisIndex: 1,
            smooth: true,
            showSymbol: false,
            lineStyle: { color: '#00BFFF', width: 2 }
          },
          {
            name: '在售数量',
            type: 'line',
            data: sellCountData,
            yAxisIndex: 1,
            smooth: true,
            showSymbol: false,
            lineStyle: { color: '#FFD700', width: 2 }
          },
          {
            name: '交易额',
            type: 'bar',
            data: turnoverData,
            yAxisIndex: 2,
            itemStyle: { color: '#FFA500', opacity: 0.5 }
          }
        ]
      })
    }

    watch(klineData, async (newVal) => {
      await nextTick() // 总是等待 DOM 更新

      // 每次数据变化时,先销毁旧的图表实例
      if (myKlineChart.value) {
        myKlineChart.value.dispose()
        myKlineChart.value = null
      }
      if (myDataChart.value) {
        myDataChart.value.dispose()
        myDataChart.value = null
      }

      if (newVal && newVal.length > 0) {
        // 如果有新数据,重新初始化图表
        initKlineChart()
        initDataChart()
      } else {
        // 如果没有数据,图表已被销毁,无需额外操作
      }
    }, { immediate: true })

    return {
      searchQuery,
      searchResults,
      selectedItem,
      priceData,
      searching,
      loadingPrice,
      klineData,
      loadingKlineData,
      klineError,
      handleSearch,
      selectItem,
      formatTime,
      klineChart,
      myKlineChart,
      dataChart,
      myDataChart,
      highestSellPrice,
      lowestBiddingPrice,
      trackItem
    }
  }
}
</script>

<style scoped>
.items-page{width:100%;max-width:1400px;padding:24px;margin:40px auto 0;animation:fadeIn .4s ease}.items-grid-container{display:grid;grid-template-columns:.8fr 2.2fr;grid-template-rows:auto auto 1fr;gap:20px;grid-template-areas:"tracking price" "search kline" "search data" "search data"}@media (max-width:900px){.items-grid-container{grid-template-columns:1fr;grid-template-rows:auto;grid-template-areas:"search" "price" "kline" "data" "tracking"}}.search-panel{grid-area:search;background:rgba(0,0,0,.4);border:1px solid #00ff41;border-radius:8px;padding:16px;display:flex;flex-direction:column}.price-panel{grid-area:price;background:rgba(0,0,0,.4);border:1px solid #00ff41;border-radius:8px;padding:16px;display:flex;flex-direction:column;min-height:250px}.kline-panel{grid-area:kline;background:rgba(0,0,0,.4);border:1px solid #00ff41;border-radius:8px;padding:16px;display:flex;flex-direction:column;min-height:450px}.kline-chart-container{width:100%;height:420px;min-height:420px}.data-panel{grid-area:data;background:rgba(0,0,0,.4);border:1px solid #00ff41;border-radius:8px;padding:16px;display:flex;flex-direction:column;min-height:450px}.data-chart-container{width:100%;height:420px;min-height:420px}.tracking-panel{grid-area:tracking;background:rgba(0,0,0,.4);border:1px solid #00ff41;border-radius:8px;padding:24px;display:flex;flex-direction:column;justify-content:center;align-items:center}.panel-title{color:#00ff41;font-family:'Courier New',monospace;font-size:24px;margin-bottom:12px}.panel-placeholder{color:rgba(0,255,65,.6);font-family:'Courier New',monospace;font-size:16px;text-align:center}.track-button{background:#00ff41;color:#000;border:none;border-radius:8px;padding:12px 24px;font-size:18px;font-weight:700;cursor:pointer;transition:all .3s ease}.track-button:hover{background:#00e63c;box-shadow:0 0 15px rgba(0,255,65,.5)}.items-header{margin-bottom:12px}.title{font-family:'Courier New',monospace;font-size:20px;font-weight:700;color:#00ff41;margin:0 0 8px 0;text-shadow:0 0 10px rgba(0,255,65,.5)}.search-box{position:relative}.search-input{width:100%;padding:10px 16px;font-size:14px;font-family:'Courier New',monospace;background:rgba(0,0,0,.6);border:2px solid #00ff41;border-radius:8px;color:#00ff41;outline:none;transition:all .3s ease}.search-input::placeholder{color:rgba(0,255,65,.4)}.search-input:focus{border-color:#00ff41;box-shadow:0 0 20px rgba(0,255,65,.3)}.search-status{position:absolute;right:20px;top:50%;transform:translateY(-50%);color:#00ff41;font-size:14px}.search-results{margin-top:24px;background:rgba(0,0,0,.4);border:1px solid #00ff41;border-radius:8px;overflow:hidden;flex-grow:1;display:flex;flex-direction:column}.results-header{padding:12px 20px;background:rgba(0,255,65,.1);border-bottom:1px solid #00ff41;color:#00ff41;font-family:'Courier New',monospace;font-size:14px}.results-list{flex-grow:1;overflow-y:auto}.result-item{padding:16px 20px;border-bottom:1px solid rgba(0,255,65,.2);cursor:pointer;transition:all .2s ease}.result-item:last-child{border-bottom:none}.result-item:hover{background:rgba(0,255,65,.1)}.result-item.selected{background:rgba(0,255,65,.2)}.item-name{color:#00ff41;font-family:'Courier New',monospace;font-size:16px;margin-bottom:4px}.item-hash{color:rgba(0,255,65,.6);font-family:'Courier New',monospace;font-size:12px}.price-details{padding:0}.details-header{margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid rgba(0,255,65,.3);display:flex;justify-content:space-between;align-items:center}.details-header h2{color:#00ff41;font-family:'Courier New',monospace;font-size:16px;margin:0}.update-time{color:rgba(0,255,65,.6);font-family:'Courier New',monospace;font-size:11px}.price-grid{display:grid;grid-template-columns:repeat(5,1fr);grid-auto-rows:minmax(min-content,max-content);gap:12px;flex-wrap:wrap}.price-card{background:rgba(0,0,0,.3);border:1px solid rgba(0,255,65,.3);border-radius:6px;padding:8px;transition:all .3s ease}.price-card:hover{border-color:#00ff41;box-shadow:0 0 15px rgba(0,255,65,.2)}.platform-name{color:#00ff41;font-family:'Courier New',monospace;font-size:13px;font-weight:700;margin-bottom:6px;text-align:center}.price-info{display:flex;flex-direction:column;gap:4px}.price-line{display:flex;align-items:center;gap:4px}.price-line .label{color:rgba(0,255,65,.7);font-family:'Courier New',monospace;font-size:11px;min-width:50px}.price-line .value.price{color:#00ff41;font-family:'Courier New',monospace;font-size:13px;font-weight:700}.price-line .count{color:rgba(0,255,65,.5);font-family:'Courier New',monospace;font-size:10px}.loading{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:60px 20px;gap:16px;color:#00ff41;font-family:'Courier New',monospace}.loading-spinner{width:40px;height:40px;border:3px solid rgba(0,255,65,.2);border-top-color:#00ff41;border-radius:50%;animation:spin 1s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}.empty-state,.placeholder-state,.error-state{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:80px 20px;gap:16px;flex-grow:1}.empty-icon,.placeholder-icon,.error-icon{font-size:64px;opacity:.5}.error-icon{color:rgba(255,100,100,.8)}.empty-text,.placeholder-text{color:rgba(0,255,65,.6);font-family:'Courier New',monospace;font-size:16px}.error-text{color:rgba(255,100,100,.8);font-family:'Courier New',monospace;font-size:16px;text-align:center}.highest-sell{color:red!important;text-shadow:0 0 8px rgba(255,0,0,.7)}.lowest-bidding{color:#ff0!important;text-shadow:0 0 8px rgba(255,255,0,.7)}.empty-card{background:rgba(0,0,0,.1);border:1px dashed rgba(0,255,65,.1);color:rgba(0,255,65,.3);display:flex;justify-content:center;align-items:center}.empty-card .platform-name,.empty-card .price-info{display:none}.results-list::-webkit-scrollbar{width:8px}.results-list::-webkit-scrollbar-track{background:rgba(0,0,0,.2)}.results-list::-webkit-scrollbar-thumb{background:rgba(0,255,65,.3);border-radius:4px}.results-list::-webkit-scrollbar-thumb:hover{background:rgba(0,255,65,.5)}
</style>
