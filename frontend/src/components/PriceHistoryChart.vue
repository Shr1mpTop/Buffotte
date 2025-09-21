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
      const times = props.series.map(p => p.time)
      const prices = props.series.map(p => p.price)

      return {
        tooltip: {
          trigger: 'axis',
          formatter: function (params) {
            const p = params[0]
            return `${p.axisValue}<br/>价格: ¥${p.data}`
          }
        },
        xAxis: {
          type: 'category',
          data: times,
          boundaryGap: false,
          axisLabel: {
            formatter: function (value) {
              const d = new Date(value)
              return d.toLocaleString()
            }
          }
        },
        yAxis: {
          type: 'value',
          axisLabel: { formatter: '¥{value}' }
        },
        series: [
          {
            name: '最低售价',
            type: 'line',
            data: prices,
            smooth: false,
            showSymbol: false,
            lineStyle: { width: 2 },
            areaStyle: { opacity: 0.05 }
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
