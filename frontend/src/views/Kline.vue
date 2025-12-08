<template>
  <div class="kline-container">
    <div class="controls">
      <div class="switch-container">
        <label for="prediction-toggle">预测</label>
        <label class="switch">
          <input type="checkbox" id="prediction-toggle" v-model="showPrediction" @change="updateChart">
          <span class="slider round"></span>
        </label>
      </div>
      <div class="switch-container">
        <label for="confidence-toggle">置信区间</label>
        <label class="switch">
          <input type="checkbox" id="confidence-toggle" v-model="showConfidence" @change="updateChart" :disabled="!showPrediction">
          <span class="slider round"></span>
        </label>
      </div>
    </div>
    <div ref="chart" class="chart"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, shallowRef, watch } from 'vue';
import * as echarts from 'echarts/core';
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  MarkPointComponent,
  MarkLineComponent
} from 'echarts/components';
import { CandlestickChart, LineChart } from 'echarts/charts';
import { CanvasRenderer } from 'echarts/renderers';
import { client } from '../services/api.js';

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
  CanvasRenderer
]);

const chart = ref(null);
const myChart = shallowRef(null);
const showPrediction = ref(true);
const showConfidence = ref(true);
let isInitialLoad = true; // Flag for initial zoom setting

const upColor = '#00ff00';
const downColor = '#ff0000';

let allData = {}; // 用于存储从 API 获取的原始数据

// ECharts 配置项
const option = {
  backgroundColor: '#000',
  title: {
    text: 'Futuristic K-Line',
    left: 'center',
    textStyle: { color: '#00ff00' }
  },
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'cross' },
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    borderColor: '#00ff00',
    textStyle: { color: '#00ff00' }
  },
  legend: {
    data: ['Daily K', 'MA5', 'MA10', 'Prediction', 'Confidence Interval'],
    top: '10%',
    textStyle: { color: '#ccc' },
    inactiveColor: '#555',
    selected: {
      'Prediction': true,
      'Confidence Interval': true
    }
  },
  grid: { left: '10%', right: '10%', bottom: '15%' },
  xAxis: {
    type: 'category',
    scale: true,
    boundaryGap: false,
    axisLine: { onZero: false, lineStyle: { color: '#8392A5' } },
    splitLine: { show: false },
    min: 'dataMin',
    max: 'dataMax'
  },
  yAxis: {
    scale: true,
    splitArea: { show: true, areaStyle: { color: ['rgba(0,0,0,0.2)', 'rgba(0,0,0,0.4)'] } },
    axisLine: { lineStyle: { color: '#8392A5' } }
  },
  dataZoom: [
    { type: 'inside', start: 50, end: 100 },
    {
      show: true,
      type: 'slider',
      top: '90%',
      start: 50,
      end: 100,
      handleIcon: 'M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z M13.3,24.4H6.7V23h6.6V24.4z M13.3,19.6H6.7v-1.4h6.6V19.6z',
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
};

// 数据处理函数
function splitData(rawData) {
  let categoryData = [];
  let values = [];
  let volumes = [];
  for (let i = 0; i < rawData.length; i++) {
    categoryData.push(new Date(rawData[i].timestamp * 1000).toLocaleDateString());
    values.push([rawData[i].open, rawData[i].close, rawData[i].low, rawData[i].high]);
    volumes.push([i, rawData[i].volume, rawData[i].open > rawData[i].close ? 1 : -1]);
  }
  return { categoryData, values, volumes };
}

function calculateMA(dayCount, data) {
  var result = [];
  for (var i = 0, len = data.length; i < len; i++) {
    if (i < dayCount) {
      result.push('-');
      continue;
    }
    var sum = 0;
    for (var j = 0; j < dayCount; j++) {
      sum += data[i - j][1]; // close price
    }
    result.push((sum / dayCount).toFixed(2));
  }
  return result;
}

function processPredictionData(predictionRaw) {
    const predictionLine = [];
    const confidenceArea = [];
    
    predictionRaw.forEach(p => {
        const date = new Date(p.timestamp * 1000).toLocaleDateString();
        const price = p.predicted_close_price;
        const std = p.rolling_std_7;

        predictionLine.push([date, price]);
        
        if (std !== null) {
            confidenceArea.push([
                date,
                price - 1.96 * std, // 95% confidence lower bound
                price + 1.96 * std  // 95% confidence upper bound
            ]);
        }
    });

    return { predictionLine, confidenceArea };
}


// 更新图表函数
function updateChart() {
  if (!myChart.value || !allData.historical) return;

  const { categoryData, values } = splitData(allData.historical);
  const { predictionLine, confidenceArea } = processPredictionData(allData.prediction);

  // 将预测数据的日期添加到 categoryData
  const combinedCategoryData = [...categoryData];
  predictionLine.forEach(p => {
    if (!combinedCategoryData.includes(p[0])) {
      combinedCategoryData.push(p[0]);
    }
  });

  const series = [
    {
      name: 'Daily K',
      type: 'candlestick',
      data: values,
      itemStyle: {
        color: upColor,
        color0: downColor,
        borderColor: upColor,
        borderColor0: downColor
      }
    },
    {
      name: 'MA5',
      type: 'line',
      data: calculateMA(5, values),
      smooth: true,
      lineStyle: { opacity: 0.5 }
    },
    {
      name: 'MA10',
      type: 'line',
      data: calculateMA(10, values),
      smooth: true,
      lineStyle: { opacity: 0.5 }
    }
  ];

  if (showPrediction.value) {
    series.push({
      name: 'Prediction',
      type: 'line',
      data: predictionLine,
      smooth: true,
      symbol: 'none',
      lineStyle: {
        color: '#00ffff',
        width: 2,
        type: 'dashed'
      }
    });

    if (showConfidence.value) {
      series.push({
        name: 'Confidence Interval',
        type: 'line',
        data: confidenceArea.map(d => [d[0], d[1]]), // Lower bound
        lineStyle: { opacity: 0 },
        stack: 'confidence',
        symbol: 'none'
      });
      series.push({
        name: 'Confidence Interval',
        type: 'line',
        data: confidenceArea.map(d => [d[0], d[2] - d[1]]), // Difference for stacking
        lineStyle: { opacity: 0 },
        areaStyle: { color: 'rgba(0, 255, 255, 0.2)' },
        stack: 'confidence',
        symbol: 'none'
      });
    }
  }

  const optionToSet = {
    xAxis: { data: combinedCategoryData },
    legend: {
      selected: {
        'Prediction': showPrediction.value,
        'Confidence Interval': showPrediction.value && showConfidence.value,
        'Daily K': true,
        'MA5': true,
        'MA10': true
      }
    },
    series: series
  };

  if (isInitialLoad && combinedCategoryData.length > 1) {
    const lastHistoricalIndex = categoryData.length > 0 ? categoryData.length - 1 : 0;
    const startIndex = Math.max(0, lastHistoricalIndex - 29); // Last 30 days of history
    const endIndex = Math.min(combinedCategoryData.length - 1, lastHistoricalIndex + 7); // Next 7 days of prediction
    
    const startPercent = (startIndex / (combinedCategoryData.length - 1)) * 100;
    const endPercent = (endIndex / (combinedCategoryData.length - 1)) * 100;

    optionToSet.dataZoom = [
        { start: startPercent, end: endPercent },
        { start: startPercent, end: endPercent }
    ];
    isInitialLoad = false;
  }

  myChart.value.setOption(optionToSet);
}

// 监听开关变化
watch([showPrediction, showConfidence], () => {
    if (!showPrediction.value) {
        showConfidence.value = false;
    }
    updateChart();
});


onMounted(async () => {
  myChart.value = echarts.init(chart.value, 'dark');
  myChart.value.setOption(option); // Set base option first
  myChart.value.showLoading();

  try {
    const response = await client.get('/kline/chart-data');
    allData = response.data;
    updateChart();
  } catch (error) {
    console.error('Failed to fetch chart data:', error);
    // You can show an error message on the chart here
  } finally {
    myChart.value.hideLoading();
  }
});

</script>

<style scoped>
.auth-page{display:flex;align-items:center;justify-content:center;height:100vh;overflow:hidden;background:#000}.auth-container{width:100%;max-width:420px;animation:fadeInUp .5s ease}@keyframes fadeInUp{from{opacity:0;transform:translateY(30px)}to{opacity:1;transform:translateY(0)}}.auth-header{text-align:center;margin-bottom:32px}.logo{color:var(--primary-green);font-size:32px;font-weight:700;letter-spacing:4px;text-shadow:0 0 20px rgba(0,255,127,.5);margin-bottom:8px;animation:glow 2s ease-in-out infinite}@keyframes glow{0%,100%{text-shadow:0 0 20px rgba(0,255,127,.5)}50%{text-shadow:0 0 30px rgba(0,255,127,.8),0 0 40px rgba(0,255,127,.4)}}.subtitle{color:var(--secondary-green);font-size:14px;opacity:.7}.auth-card{background:rgba(0,0,0,.8);border:1px solid rgba(0,255,127,.2);border-radius:8px;padding:32px;box-shadow:0 0 40px rgba(0,255,127,.1)}.card-title{color:var(--primary-green);font-size:18px;font-weight:600;margin-bottom:24px;padding-bottom:12px;border-bottom:1px solid rgba(0,255,127,.1)}.auth-form,.form-group{margin-bottom:20px}.form-label{display:block;color:rgba(0,255,127,.7);font-size:13px;margin-bottom:8px;font-weight:500}.form-input{width:100%;background:rgba(0,255,127,.05);border:1px solid rgba(0,255,127,.2);padding:12px 16px;color:var(--primary-green);border-radius:6px;font-family:'Source Code Pro',monospace;font-size:14px;transition:all .2s}.form-input:focus{outline:none;border-color:var(--primary-green);background:rgba(0,255,127,.08);box-shadow:0 0 10px rgba(0,255,127,.2)}.form-input::placeholder{color:rgba(0,255,127,.3)}.submit-btn{width:100%;padding:14px;background:linear-gradient(45deg,var(--primary-green),var(--secondary-green));color:#000;border:none;border-radius:6px;font-weight:600;font-size:15px;cursor:pointer;transition:all .2s;font-family:'Source Code Pro',monospace}.submit-btn:hover{transform:translateY(-2px);box-shadow:0 4px 20px rgba(0,255,127,.3)}.auth-footer{text-align:center;padding-top:20px;border-top:1px solid rgba(0,255,127,.1)}.hint{color:rgba(0,255,127,.5);font-size:13px}.link{color:var(--primary-green);text-decoration:none;margin-left:8px;font-weight:500}.link:hover{text-decoration:underline}
</style>
