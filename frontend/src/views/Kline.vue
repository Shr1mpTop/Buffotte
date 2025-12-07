<template>
  <div class="kline">
    <div class="kline-header">
      <h1 class="title">$ ./kline_monitor.sh</h1>
      <div class="stats-bar">
        <span class="stat-item">TOTAL: {{ totalDays }} DAYS</span>
        <span class="stat-item">RANGE: {{ dateRange }}</span>
        <button class="refresh-btn" @click="refreshData" :disabled="isRefreshing">
          <span v-if="!isRefreshing">REFRESH</span>
          <span v-else>⏳ LOADING...</span>
        </button>
      </div>
      <div v-if="toastMessage" class="toast" :class="{ show: showToast }">
        {{ toastMessage }}
      </div>
    </div>
    <div class="kline-content">
      <div class="chart-container">
        <v-chart :option="chartOption" :autoresize="true" />
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { CandlestickChart } from 'echarts/charts'
import { DataZoomComponent, GridComponent, TooltipComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import axios from 'axios'

use([
  CanvasRenderer,
  CandlestickChart,
  DataZoomComponent,
  GridComponent,
  TooltipComponent
])

export default {
  name: 'Kline',
  components: {
    VChart
  },
  setup() {
    const totalDays = ref(0)
    const dateRange = ref('')
    const isRefreshing = ref(false)
    const toastMessage = ref('')
    const showToast = ref(false)
    const refreshTimestamps = ref([])
    
    const chartOption = ref({
      backgroundColor: 'transparent',
      grid: {
        left: '60px',
        right: '60px',
        bottom: '80px',
        top: '40px'
      },
      xAxis: {
        type: 'time',
        min: function(value) {
          return value.min
        },
        max: function(value) {
          // X轴最大值向未来偏移一天
          return value.max + 24 * 3600 * 1000
        },
        axisLine: {
          lineStyle: {
            color: 'rgba(0, 255, 127, 0.5)',
            width: 2
          }
        },
        axisLabel: {
          color: 'rgba(0, 255, 127, 0.8)',
          formatter: function(value) {
            // 直接使用UTC日期，因为数据点已经在23:55:10
            const date = new Date(value)
            const year = date.getUTCFullYear()
            const month = String(date.getUTCMonth() + 1).padStart(2, '0')
            const day = String(date.getUTCDate()).padStart(2, '0')
            return `${year}-${month}-${day}`
          },
          rotate: 45,
          fontSize: 11,
          fontFamily: 'monospace'
        },
        splitLine: {
          show: false
        }
      },
      yAxis: {
        type: 'value',
        scale: true,
        axisLine: {
          lineStyle: {
            color: 'rgba(0, 255, 127, 0.5)',
            width: 2
          }
        },
        axisLabel: {
          color: 'rgba(0, 255, 127, 0.8)',
          fontSize: 11,
          fontFamily: 'monospace',
          formatter: '{value}'
        },
        splitLine: {
          lineStyle: {
            color: 'rgba(0, 255, 127, 0.08)',
            type: 'dashed'
          }
        }
      },
      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: [0],
          start: 0,
          end: 100,
          minValueSpan: 3600 * 24 * 1000 * 7 // 最小7天
        },
        {
          show: true,
          xAxisIndex: [0],
          type: 'slider',
          bottom: '10px',
          start: 0,
          end: 100,
          height: 30,
          handleIcon: 'path://M10.7,11.9H9.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4h1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z',
          handleSize: '100%',
          handleStyle: {
            color: 'rgba(0, 255, 127, 0.6)',
            shadowColor: 'rgba(0, 255, 127, 0.4)',
            shadowBlur: 10
          },
          textStyle: {
            color: 'rgba(0, 255, 127, 0.7)',
            fontFamily: 'monospace'
          },
          borderColor: 'rgba(0, 255, 127, 0.3)',
          fillerColor: 'rgba(0, 255, 127, 0.1)',
          dataBackground: {
            lineStyle: {
              color: 'rgba(0, 255, 127, 0.3)'
            },
            areaStyle: {
              color: 'rgba(0, 255, 127, 0.1)'
            }
          }
        }
      ],
      series: [
        {
          name: 'K线',
          type: 'candlestick',
          data: [],
          itemStyle: {
            color: '#00ff7f',
            color0: '#ff4444',
            borderColor: '#00ff7f',
            borderColor0: '#ff4444',
            borderWidth: 1.5
          },
          emphasis: {
            itemStyle: {
              color: '#00ffaa',
              color0: '#ff6666',
              borderColor: '#00ffaa',
              borderColor0: '#ff6666',
              borderWidth: 2,
              shadowColor: 'rgba(0, 255, 127, 0.5)',
              shadowBlur: 10
            }
          }
        }
      ],
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
          lineStyle: {
            color: 'rgba(0, 255, 127, 0.5)',
            type: 'dashed'
          }
        },
        backgroundColor: 'rgba(0, 0, 0, 0.95)',
        borderColor: 'rgba(0, 255, 127, 0.6)',
        borderWidth: 2,
        textStyle: {
          color: '#00ff7f',
          fontFamily: 'monospace',
          fontSize: 12
        },
        padding: 12,
        formatter: function (params) {
          if (!params || !params[0]) return ''
          const data = params[0].data
          const timestamp = data[0]
          // 使用UTC方法获取正确的日期
          const date = new Date(timestamp)
          const year = date.getUTCFullYear()
          const month = String(date.getUTCMonth() + 1).padStart(2, '0')
          const day = String(date.getUTCDate()).padStart(2, '0')
          const dateStr = `${year}-${month}-${day}`
          
          const change = ((data[2] - data[1]) / data[1] * 100).toFixed(2)
          const changeColor = change >= 0 ? '#00ff7f' : '#ff4444'
          const changeSymbol = change >= 0 ? '+' : ''
          
          return `
            <div style="font-family: monospace;">
              <div style="border-bottom: 1px solid rgba(0, 255, 127, 0.3); padding-bottom: 6px; margin-bottom: 6px;">
                <span style="color: #00ff7f;">📅 ${dateStr}</span>
              </div>
              <div style="margin: 4px 0;">开盘: <span style="color: #00ffaa;">${data[1].toFixed(2)}</span></div>
              <div style="margin: 4px 0;">收盘: <span style="color: #00ffaa;">${data[2].toFixed(2)}</span></div>
              <div style="margin: 4px 0;">最低: <span style="color: #00ffaa;">${data[3].toFixed(2)}</span></div>
              <div style="margin: 4px 0;">最高: <span style="color: #00ffaa;">${data[4].toFixed(2)}</span></div>
              <div style="margin-top: 8px; padding-top: 6px; border-top: 1px solid rgba(0, 255, 127, 0.3);">
                涨跌幅: <span style="color: ${changeColor}; font-weight: bold;">${changeSymbol}${change}%</span>
              </div>
            </div>
          `
        }
      }
    })

    const loadKlineData = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/kline/data')
        const data = response.data.data
        const klineData = []
        let minTime = Infinity
        let maxTime = -Infinity
        
        data.forEach(item => {
          // 后端返回的timestamp已经是UTC+8时间戳，直接转换为毫秒
          const timestamp = item.timestamp * 1000
          klineData.push([timestamp, item.open, item.close, item.low, item.high])
          if (timestamp < minTime) minTime = timestamp
          if (timestamp > maxTime) maxTime = timestamp
        })
        
        chartOption.value.series[0].data = klineData

        // 计算统计信息
        totalDays.value = data.length
        const startDate = new Date(minTime)
        const endDate = new Date(maxTime)
        dateRange.value = `${startDate.toLocaleDateString()} - ${endDate.toLocaleDateString()}`

        // 根据时间范围动态设置X轴标签间隔
        const timeRange = maxTime - minTime
        const days = timeRange / (24 * 3600 * 1000)
        let interval
        if (days <= 30) {
          interval = 2 * 24 * 3600 * 1000 // 每2天
        } else if (days <= 90) {
          interval = 7 * 24 * 3600 * 1000 // 每周
        } else {
          interval = 14 * 24 * 3600 * 1000 // 每两周
        }
        chartOption.value.xAxis.axisLabel.interval = interval
      } catch (error) {
        console.error('加载K线数据失败:', error)
      }
    }

    const showToastMessage = (message) => {
      toastMessage.value = message
      showToast.value = true
      setTimeout(() => {
        showToast.value = false
      }, 3000)
    }

    const refreshData = async () => {
      // 检查速率限制：1分钟内最多3次
      const now = Date.now()
      const oneMinuteAgo = now - 60000
      
      // 清除1分钟前的记录
      refreshTimestamps.value = refreshTimestamps.value.filter(t => t > oneMinuteAgo)
      
      if (refreshTimestamps.value.length >= 3) {
        showToastMessage('⚠️ 点击太快了，休息一下吧~')
        return
      }
      
      isRefreshing.value = true
      try {
        // 调用后端刷新接口
        const refreshResponse = await axios.post('http://localhost:8000/api/kline/refresh')
        if (refreshResponse.data.success) {
          // 刷新成功后重新加载数据
          await loadKlineData()
          refreshTimestamps.value.push(now)
          showToastMessage('✅ 数据刷新成功')
        }
      } catch (error) {
        console.error('刷新数据失败:', error)
        showToastMessage('❌ 刷新失败: ' + (error.response?.data?.detail || error.message))
      } finally {
        isRefreshing.value = false
      }
    }

    onMounted(() => {
      loadKlineData()
    })

    return {
      chartOption,
      totalDays,
      dateRange,
      isRefreshing,
      toastMessage,
      showToast,
      refreshData
    }
  }
}
</script>

<style scoped>
.kline {
  width: 100%;
  max-width: 1400px;
  padding: 24px;
  margin: 40px auto 0;
  animation: fadeIn 0.6s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.kline-header {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid rgba(0, 255, 127, 0.3);
}

.title {
  color: #00ff7f;
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 12px 0;
  font-family: 'Courier New', monospace;
  text-shadow: 0 0 15px rgba(0, 255, 127, 0.4);
  letter-spacing: 1px;
}

.stats-bar {
  display: flex;
  gap: 24px;
  margin-top: 12px;
}

.stat-item {
  color: rgba(0, 255, 127, 0.8);
  font-size: 13px;
  font-family: 'Courier New', monospace;
  padding: 6px 12px;
  background: rgba(0, 255, 127, 0.05);
  border: 1px solid rgba(0, 255, 127, 0.2);
  border-radius: 4px;
  letter-spacing: 0.5px;
}

.refresh-btn {
  color: rgba(0, 255, 127, 0.9);
  font-size: 13px;
  font-family: 'Courier New', monospace;
  padding: 6px 16px;
  background: rgba(0, 255, 127, 0.1);
  border: 1px solid rgba(0, 255, 127, 0.4);
  border-radius: 4px;
  letter-spacing: 0.5px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 600;
}

.refresh-btn:hover:not(:disabled) {
  background: rgba(0, 255, 127, 0.2);
  border-color: rgba(0, 255, 127, 0.6);
  box-shadow: 0 0 10px rgba(0, 255, 127, 0.3);
  transform: translateY(-1px);
}

.refresh-btn:active:not(:disabled) {
  transform: translateY(0);
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.toast {
  position: fixed;
  top: 100px;
  left: 50%;
  transform: translateX(-50%) translateY(-100px);
  background: rgba(0, 0, 0, 0.95);
  color: #00ff7f;
  padding: 12px 24px;
  border-radius: 6px;
  border: 2px solid rgba(0, 255, 127, 0.5);
  font-family: 'Courier New', monospace;
  font-size: 14px;
  box-shadow: 0 0 20px rgba(0, 255, 127, 0.3);
  opacity: 0;
  transition: all 0.4s ease;
  z-index: 10000;
  pointer-events: none;
}

.toast.show {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}

.kline-content {
  display: flex;
  justify-content: center;
}

.chart-container {
  width: 100%;
  height: 650px;
  background: rgba(0, 0, 0, 0.7);
  border: 2px solid rgba(0, 255, 127, 0.3);
  border-radius: 8px;
  padding: 20px;
  box-shadow: 
    0 0 20px rgba(0, 255, 127, 0.1),
    inset 0 0 30px rgba(0, 255, 127, 0.03);
  position: relative;
}

.chart-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    linear-gradient(90deg, transparent 0%, rgba(0, 255, 127, 0.02) 50%, transparent 100%),
    linear-gradient(0deg, transparent 0%, rgba(0, 255, 127, 0.02) 50%, transparent 100%);
  pointer-events: none;
  border-radius: 6px;
}
</style>
