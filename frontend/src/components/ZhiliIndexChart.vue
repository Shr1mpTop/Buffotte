<template>
  <div class="zhili-index-dashboard">
    <!-- 顶部信息栏 -->
    <div class="index-header">
      <div class="index-info">
        <h2 class="index-name">🎯 致力指数</h2>
        <div class="index-value" :class="{ 'positive': changePercent >= 0, 'negative': changePercent < 0 }">
          {{ currentIndex.toFixed(2) }}
        </div>
        <div class="index-change" :class="{ 'positive': changePercent >= 0, 'negative': changePercent < 0 }">
          <span class="change-value">{{ changeValue >= 0 ? '+' : '' }}{{ changeValue.toFixed(2) }}</span>
          <span class="change-percent">({{ changePercent >= 0 ? '+' : '' }}{{ changePercent.toFixed(2) }}%)</span>
        </div>
      </div>
      <div class="market-info">
        <div class="info-item">
          <span class="label">市值总量</span>
          <span class="value">{{ formatMarketCap(currentMarketCap) }}</span>
        </div>
        <div class="info-item">
          <span class="label">饰品总数</span>
          <span class="value">{{ currentItemCount.toLocaleString() }}</span>
        </div>
        <div class="info-item">
          <span class="label">平均价格</span>
          <span class="value">¥{{ currentAvgPrice.toFixed(2) }}</span>
        </div>
      </div>
    </div>

    <!-- 控制栏 -->
    <div class="chart-controls">
      <div class="time-range-selector">
        <label>时间周期:</label>
        <select v-model="selectedRange" @change="updateRange">
          <option value="7">1周</option>
          <option value="30">1个月</option>
          <option value="90">3个月</option>
          <option value="180">6个月</option>
          <option value="365">1年</option>
        </select>
      </div>
      <div class="chart-type-selector">
        <label>图表类型:</label>
        <select v-model="chartType">
          <option value="candle">K线图</option>
          <option value="line">折线图</option>
        </select>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="chart-container">
      <v-chart 
        :option="chartOption" 
        :style="{ width: '100%', height: '500px' }"
        autoresize
      />
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import VChart from 'vue-echarts'

export default {
  name: 'ZhiliIndexChart',
  components: {
    VChart
  },
  props: {
    data: {
      type: Array,
      default: () => []
    }
  },
  emits: ['range-change'],
  setup(props, { emit }) {
    const selectedRange = ref('30') // 默认1个月
    const chartType = ref('candle') // 默认K线图

    const filteredData = computed(() => {
      if (!props.data || props.data.length === 0) {
        return []
      }

      const days = parseInt(selectedRange.value)
      const now = new Date()
      const cutoffDate = new Date(now.getTime() - days * 24 * 60 * 60 * 1000)

      return props.data.filter(item => {
        const itemDate = new Date(item.date)
        return itemDate >= cutoffDate
      })
    })

    const updateRange = () => {
      emit('range-change', selectedRange.value)
    }

    // 当前数据
    const currentData = computed(() => {
      const data = filteredData.value
      if (data.length > 0) {
        const latest = data[data.length - 1]
        return {
          zhiliIndex: latest.zhiliIndex || 10000,
          marketCap: latest.marketCap || 0,
          itemCount: latest.itemCount || 0,
          avgPrice: latest.avgPrice || 0
        }
      }
      return {
        zhiliIndex: 10000,
        marketCap: 0,
        itemCount: 0,
        avgPrice: 0
      }
    })

    const currentIndex = computed(() => currentData.value.zhiliIndex)
    const currentMarketCap = computed(() => currentData.value.marketCap)
    const currentItemCount = computed(() => currentData.value.itemCount)
    const currentAvgPrice = computed(() => currentData.value.avgPrice)

    // 计算涨跌
    const changeValue = computed(() => {
      const data = filteredData.value
      if (data.length < 2) return 0
      const current = data[data.length - 1].zhiliIndex || 0
      const previous = data[data.length - 2].zhiliIndex || 0
      return current - previous
    })

    const changePercent = computed(() => {
      const data = filteredData.value
      if (data.length < 2) return 0
      const previous = data[data.length - 2].zhiliIndex || 0
      return previous > 0 ? (changeValue.value / previous) * 100 : 0
    })

    const formatMarketCap = (value) => {
      if (value == null || value === undefined) {
        return '暂无'
      }
      if (value >= 100000000) {
        return (value / 100000000).toFixed(2) + '亿'
      } else if (value >= 10000) {
        return (value / 10000).toFixed(1) + '万'
      }
      return value.toFixed(0)
    }

    const chartOption = computed(() => {
      const data = filteredData.value

      if (!data || data.length === 0) {
        return {
          title: {
            text: '暂无数据',
            left: 'center',
            top: 'center'
          }
        }
      }

      // 准备数据
      const dates = data.map(item => item.date)
      const indices = data.map(item => item.zhiliIndex)
      const marketValues = data.map(item => item.marketCap)
      
      // 准备柱状图数据（指数）
      const barData = indices // 所有指数数据
      
      // 准备散点图数据（市值）
      const scatterData = marketValues.map((value, index) => [index, value])

      return {
        title: {
          text: '🎯 致力指数K线图',
          left: 'center',
          textStyle: {
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        tooltip: {
          trigger: 'axis',
          formatter: (params) => {
            const item = data[params[0].dataIndex]
            let result = `<div style="font-weight: bold;">${params[0].name}</div>`
            
            params.forEach(param => {
              if (param.seriesName === '指数') {
                result += `<div>� 指数: ${param.value}</div>`
              } else if (param.seriesName === '市值') {
                result += `<div>💰 市值: ¥${param.value.toLocaleString()}</div>`
              }
            })
            
            return result
          }
        },
        legend: {
          data: ['指数', '市值'],
          top: 30
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: dates,
          name: '日期',
          nameLocation: 'middle',
          nameGap: 30
        },
        yAxis: [
          {
            type: 'value',
            name: '指数值',
            nameLocation: 'middle',
            nameGap: 50,
            axisLabel: {
              formatter: '{value}'
            },
            position: 'left'
          },
          {
            type: 'value',
            name: '市值(亿)',
            nameLocation: 'middle',
            nameGap: 50,
            axisLabel: {
              formatter: (value) => (value / 100000000).toFixed(1) + '亿'
            },
            position: 'right'
          }
        ],
        series: [
          {
            name: '指数',
            type: 'bar',
            data: barData,
            yAxisIndex: 0,
            itemStyle: (params) => {
              const currentValue = indices[params.dataIndex]
              const prevValue = params.dataIndex > 0 ? indices[params.dataIndex - 1] : currentValue
              return {
                color: currentValue >= prevValue ? '#ee6666' : '#91cc75', // 红涨绿跌
                borderRadius: [4, 4, 0, 0]
              }
            },
            emphasis: {
              itemStyle: {
                opacity: 0.8
              }
            }
          },
          {
            name: '市值',
            type: 'line',
            data: scatterData,
            yAxisIndex: 1,
            symbol: 'circle',
            symbolSize: 8,
            showSymbol: true,
            lineStyle: {
              width: 3,
              color: '#ffa500'  // 橙色，与红绿形成反差
            },
            itemStyle: {
              color: '#ffa500'
            },
            smooth: true,
            markLine: {
              data: [
                {
                  name: '基准线',
                  yAxis: 10000,
                  lineStyle: {
                    color: '#ee6666',
                    type: 'dashed',
                    width: 2
                  },
                  label: {
                    formatter: '基准值: 10000',
                    position: 'end'
                  }
                }
              ]
            }
          }
        ]
      }
    })

    const currentMarketValue = computed(() => {
      const data = filteredData.value
      if (data.length > 0) {
        const latest = data[data.length - 1].marketCap
        return (latest / 100000000).toFixed(1) + '亿'
      }
      return '暂无'
    })

    const baseMarketValue = computed(() => {
      return '10亿'  // 基准值10000对应的市值，假设是10亿
    })

    return {
      chartOption,
      selectedRange,
      chartType,
      updateRange,
      currentIndex,
      currentMarketCap,
      currentItemCount,
      currentAvgPrice,
      changeValue,
      changePercent,
      formatMarketCap
    }
  }
}
</script>

<style scoped>
.zhili-index-dashboard {
  width: 100%;
  margin: 20px 0;
  background: #1a1a1a;
  border-radius: 12px;
  border: 1px solid #333;
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
  padding: 20px;
}

.zhili-index-dashboard:hover {
  border-color: #555;
  box-shadow: 0 6px 25px rgba(0,0,0,0.4);
}

.index-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #333;
}

.index-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.index-name {
  font-size: 18px;
  font-weight: bold;
  color: #ffffff;
  margin: 0;
}

.index-value {
  font-size: 32px;
  font-weight: bold;
  margin: 0;
  font-family: 'Courier New', monospace;
}

.index-value.positive {
  color: #ff6b6b;
}

.index-value.negative {
  color: #4ade80;
}

.index-change {
  font-size: 14px;
  margin: 0;
  font-weight: 600;
}

.index-change.positive {
  color: #ff6b6b;
}

.index-change.negative {
  color: #4ade80;
}

.market-info {
  display: flex;
  gap: 20px;
}

.info-item {
  text-align: center;
  background: #2a2a2a;
  padding: 10px 15px;
  border-radius: 6px;
  border: 1px solid #444;
  min-width: 100px;
}

.info-item:hover {
  background: #333;
  border-color: #666;
}

.info-item .label {
  font-size: 12px;
  color: #cccccc;
  margin-bottom: 4px;
  font-weight: 500;
}

.info-item .value {
  font-size: 16px;
  font-weight: bold;
  color: #4ecdc4;
  font-family: 'Courier New', monospace;
}

.chart-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  gap: 15px;
  padding: 15px;
  background: #2a2a2a;
  border-radius: 8px;
  border: 1px solid #444;
}

.time-range-selector,
.chart-type-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.time-range-selector label,
.chart-type-selector label {
  font-weight: 500;
  color: #ffffff;
  font-size: 14px;
}

.time-range-selector select,
.chart-type-selector select {
  padding: 6px 10px;
  border: 1px solid #555;
  border-radius: 6px;
  background: #1a1a1a;
  color: #ffffff;
  font-size: 14px;
  cursor: pointer;
  min-width: 80px;
  transition: all 0.3s ease;
}

.time-range-selector select:focus,
.chart-type-selector select:focus {
  outline: none;
  border-color: #4ecdc4;
  box-shadow: 0 0 0 2px rgba(78, 205, 196, 0.2);
}

.time-range-selector select:hover,
.chart-type-selector select:hover {
  border-color: #666;
}

.chart-container {
  width: 100%;
  height: 500px;
  background: #1a1a1a;
  border-radius: 8px;
  border: 1px solid #333;
  padding: 10px;
}

/* ECharts 主题覆盖 */
:deep(.echarts-for-react) {
  background: transparent !important;
}

/* 自定义滚动条 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #2a2a2a;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #666;
}
</style>