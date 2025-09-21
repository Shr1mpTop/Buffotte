<template>
  <div class="history-chart">
    <v-chart :option="chartOption" :style="{ width: '100%', height: '240px' }" autoresize />
  </div>
</template>

<script>
import { computed } from 'vue'
import VChart from 'vue-echarts'

export default {
  name: 'PriceHistoryChart',
  components: { VChart },
  props: {
    series: {
      type: Array,
      default: () => [] // [{time: '2025-09-20T12:00:00Z', price: 1.23}, ...]
    }
  },
  setup(props) {
    const chartOption = computed(() => {
      // transform to [time, price] pairs; ensure ISO strings are accepted
      const data = props.series
        .map(p => ({ t: new Date(p.time).getTime(), price: p.price }))
        .filter(p => !Number.isNaN(p.t) && typeof p.price === 'number')
        .map(p => [p.t, p.price])

      return {
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'cross' },
          formatter: function (params) {
            if (!params || !params.length) return ''
            const p = params[0]
            const date = new Date(p.data[0])
            return `${date.toLocaleString()}<br/>价格: ¥${p.data[1].toFixed(2)}`
          }
        },
        dataZoom: [
          { type: 'inside', xAxisIndex: 0, throttle: 50 },
          { type: 'slider', xAxisIndex: 0 }
        ],
        xAxis: {
          type: 'time',
          boundaryGap: false,
          axisLabel: {
            formatter: function (value) {
              const d = new Date(value)
              return d.toLocaleString()
            }
          }
        },
        yAxis: (() => {
          // filter non-finite and extreme values
          const prices = data
            .map(p => Number(p[1]))
            .filter(v => Number.isFinite(v) && Math.abs(v) < 1e7)

          if (prices.length === 0) {
            return { type: 'value', axisLabel: { formatter: value => `¥${value}` } }
          }

          // remove outliers using IQR rule
          const sorted = prices.slice().sort((a, b) => a - b)
          const q1 = sorted[Math.floor((sorted.length - 1) * 0.25)]
          const q3 = sorted[Math.floor((sorted.length - 1) * 0.75)]
          const iqr = q3 - q1
          const lowerFence = q1 - 1.5 * iqr
          const upperFence = q3 + 1.5 * iqr
          const filtered = sorted.filter(v => v >= lowerFence && v <= upperFence)

          if (filtered.length === 0) {
            return { type: 'value', axisLabel: { formatter: value => `¥${value}` } }
          }

          const minPrice = Math.min(...filtered)
          const maxPrice = Math.max(...filtered)

          const yMin = minPrice * 0.8
          const yMax = maxPrice * 1.2

          if (!Number.isFinite(yMin) || !Number.isFinite(yMax) || yMin >= yMax) {
            return { type: 'value', axisLabel: { formatter: value => `¥${value}` } }
          }

          return {
            type: 'value',
            min: yMin,
            max: yMax,
            axisLabel: { formatter: value => `¥${value}` }
          }
        })(),
        series: [
          {
            name: '最低售价',
            type: 'line',
            data: data,
            smooth: false,
            showSymbol: false,
            lineStyle: { width: 2 },
            areaStyle: { opacity: 0.06 }
          }
        ],
        grid: { left: '6%', right: '4%', top: '8%', bottom: '6%' }
      }
    })

    return { chartOption }
  }
}
</script>

<style scoped>
.history-chart { padding-top: 12px }
</style>
