import { createApp } from 'vue'
import App from './App.vue'
import './style.css'
import './css/index.css'

// 引入 ECharts
import { use } from 'echarts/core'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent
} from 'echarts/components'
import {
  PieChart,
  LineChart,
  BarChart,
  ScatterChart
} from 'echarts/charts'
import {
  CanvasRenderer
} from 'echarts/renderers'
import { GridComponent, DataZoomComponent } from 'echarts/components'

use([
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  PieChart,
  LineChart,
  BarChart,
  ScatterChart,
  GridComponent,
  DataZoomComponent,
  CanvasRenderer
])

createApp(App).mount('#app')