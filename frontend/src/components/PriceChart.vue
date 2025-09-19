<template>
  <div class="chart-container">
    <v-chart 
      :option="chartOption" 
      :style="{ width: '100%', height: '400px' }"
      autoresize
    />
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import VChart from 'vue-echarts'

export default {
  name: 'PriceChart',
  components: {
    VChart
  },
  props: {
    data: {
      type: Array,
      default: () => []
    }
  },
  setup(props) {
    const chartOption = computed(() => ({
      title: {
        text: '',
        left: 'center'
      },
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b} : {c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        left: 'left',
        data: props.data.map(item => item.name)
      },
      series: [
        {
          name: '饰品数量',
          type: 'pie',
          radius: '55%',
          center: ['50%', '60%'],
          data: props.data,
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          },
          itemStyle: {
            borderRadius: 5,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: {
            formatter: '{b}\n{c}件 ({d}%)'
          }
        }
      ],
      color: [
        '#5470c6',
        '#91cc75', 
        '#fac858',
        '#ee6666',
        '#73c0de',
        '#3ba272',
        '#fc8452',
        '#9a60b4'
      ]
    }))

    return {
      chartOption
    }
  }
}
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: 400px;
}
</style>