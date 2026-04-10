<template>
  <div class="market-page">
    <!-- Matrix rain background -->
    <canvas ref="matrixCanvas" class="matrix-bg"></canvas>
    <!-- Scanlines overlay -->
    <div class="scanlines"></div>

    <!-- HEADER -->
    <header ref="headerEl" class="hdr">
      <div class="hdr-prompt">
        <span class="p-usr">root</span><span class="p-at">@</span
        ><span class="p-host">buffotte</span><span class="p-sep">:~#&nbsp;</span
        ><span class="p-cmd">./market.sh</span><span class="p-cur">█</span>
      </div>
      <div class="hdr-meta">
        <span class="hm-dot" :class="{ pulse: isLive }"></span>
        {{ isLive ? 'LIVE' : 'OFFLINE' }} &nbsp;·&nbsp; {{ currentTime }}
      </div>
    </header>

    <!-- 核心指标卡片 -->
    <div ref="stripEl" class="stats-strip">
      <div class="stat-card" v-for="s in statsCards" :key="s.label">
        <div class="sc-label">{{ s.label }}</div>
        <div class="sc-value" :class="s.class" :ref="el => { if (el) statRefs[s.key] = el }">
          {{ s.value }}
        </div>
        <div class="sc-sub" v-if="s.sub">{{ s.sub }}</div>
      </div>
    </div>

    <!-- K线主图 -->
    <div ref="klinePanel" class="kline-panel">
      <div class="kline-header">
        <span class="kh-title">CS2 大盘指数</span>
        <div class="kline-controls">
        <div class="switch-container">
          <label>预测</label>
          <label class="switch">
            <input type="checkbox" v-model="showPrediction" @change="updateChart">
            <span class="slider round"></span>
          </label>
        </div>
        <div class="switch-container">
          <label>置信区间</label>
          <label class="switch">
            <input type="checkbox" v-model="showConfidence" @change="updateChart" :disabled="!showPrediction">
            <span class="slider round"></span>
          </label>
        </div>
        </div>
      </div>
      <div ref="chart" class="chart"></div>
    </div>

    <!-- 底部三列看板 -->
    <div ref="bottomPanel" class="bottom-grid">
      <!-- 迷你趋势图 -->
      <div class="panel-card">
        <div class="pc-hd"><span class="pc-dot"></span>7日走势</div>
        <div ref="miniChart" class="mini-chart"></div>
      </div>

      <!-- LLM 大盘分析 -->
      <div class="panel-card analysis-card">
        <div class="pc-hd">
          <span class="pc-dot"></span>AI 大盘分析
          <span class="analysis-date" v-if="analysisDate">{{ analysisDate }}</span>
        </div>
        <div class="analysis-body" v-if="marketAnalysis">
          <div class="analysis-text" v-html="renderedAnalysis"></div>
        </div>
        <div class="analysis-empty" v-else>
          <div class="empty-icon">🤖</div>
          <div>暂无AI分析数据</div>
        </div>
      </div>

      <!-- 数据分析看板 -->
      <div class="panel-card">
        <div class="pc-hd"><span class="pc-dot"></span>数据分析</div>
        <div class="data-rows" v-if="dataMetrics">
          <div class="dr" v-for="m in dataMetrics" :key="m.label">
            <span class="dr-k">{{ m.label }}</span>
            <span class="dr-v" :class="m.class">{{ m.value }}</span>
          </div>
        </div>
        <div class="analysis-empty" v-else>
          <div class="empty-icon">📊</div>
          <div>等待数据加载</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, shallowRef, reactive, computed, onMounted, onUnmounted, nextTick, watch } from 'vue';
import * as echarts from 'echarts/core';
import {
  TitleComponent, TooltipComponent, LegendComponent, GridComponent,
  DataZoomComponent, MarkPointComponent, MarkLineComponent
} from 'echarts/components';
import { CandlestickChart, LineChart, BarChart } from 'echarts/charts';
import { CanvasRenderer } from 'echarts/renderers';
import { client } from '../services/api.js';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import gsap from 'gsap';

echarts.use([
  TitleComponent, TooltipComponent, LegendComponent, GridComponent,
  DataZoomComponent, MarkPointComponent, MarkLineComponent,
  CandlestickChart, LineChart, BarChart, CanvasRenderer
]);

// Refs
const matrixCanvas = ref(null);
const headerEl = ref(null);
const stripEl = ref(null);
const klinePanel = ref(null);
const bottomPanel = ref(null);
const chart = ref(null);
const miniChart = ref(null);
const myChart = shallowRef(null);
const myMiniChart = shallowRef(null);
const statRefs = reactive({});

// State
const showPrediction = ref(true);
const showConfidence = ref(true);
const isLive = ref(true);
const currentTime = ref('');
const marketAnalysis = ref('');
const analysisDate = ref(null);
const allData = ref({ historical: [], prediction: [] });
let matrixAnimId = null;
let pollTimer = null;

// Colors
const upColor = '#00ff00';
const downColor = '#ff0000';

// --- Core metrics ---
const latestData = ref(null);
const prevData = ref(null);

const statsCards = computed(() => {
  const ld = latestData.value;
  if (!ld) return [
    { label: '最新指数', value: '--', key: 'price' },
    { label: '日涨跌幅', value: '--', key: 'change' },
    { label: '成交量', value: '--', key: 'volume' },
    { label: '成交额', value: '--', key: 'turnover' },
    { label: '振幅', value: '--', key: 'amplitude' },
  ];
  const pd = prevData.value;
  const change = pd ? ((ld.close - pd.close) / pd.close * 100) : 0;
  const amplitude = ld.open > 0 ? ((ld.high - ld.low) / ld.open * 100) : 0;
  const cls = change >= 0 ? 'up' : 'down';
  return [
    { label: '最新指数', value: ld.close.toFixed(2), key: 'price', class: cls },
    { label: '日涨跌幅', value: `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`, key: 'change', class: cls, sub: pd ? `昨日 ${pd.close.toFixed(2)}` : '' },
    { label: '成交量', value: ld.volume.toLocaleString(), key: 'volume' },
    { label: '成交额', value: formatTurnover(ld.turnover), key: 'turnover' },
    { label: '振幅', value: `${amplitude.toFixed(2)}%`, key: 'amplitude' },
  ];
});

const dataMetrics = computed(() => {
  const hist = allData.value.historical;
  if (!hist || hist.length < 2) return null;
  const closes = hist.map(h => h.close);
  const volumes = hist.map(h => h.volume);
  const last30 = hist.slice(-30);
  const last30closes = last30.map(h => h.close);
  const avg30 = last30closes.reduce((a, b) => a + b, 0) / last30closes.length;
  const avgVol = volumes.slice(-30).reduce((a, b) => a + b, 0) / 30;
  const high = Math.max(...closes);
  const low = Math.min(...closes);

  const pred = allData.value.prediction;
  let predInfo = '--';
  let predClass = '';
  if (pred && pred.length > 0) {
    const nextP = pred[0].predicted_close_price;
    const currentClose = closes[closes.length - 1];
    const pct = ((nextP - currentClose) / currentClose * 100);
    predInfo = `${nextP.toFixed(2)} (${pct >= 0 ? '+' : ''}${pct.toFixed(2)}%)`;
    predClass = pct >= 0 ? 'up' : 'down';
  }

  return [
    { label: '30日均价', value: avg30.toFixed(2) },
    { label: '历史最高', value: high.toFixed(2) },
    { label: '历史最低', value: low.toFixed(2) },
    { label: '30日均量', value: Math.round(avgVol).toLocaleString() },
    { label: '数据点数', value: hist.length.toLocaleString() },
    { label: '预测明日', value: predInfo, class: predClass },
  ];
});

const renderedAnalysis = computed(() => {
  if (!marketAnalysis.value) return '';
  return DOMPurify.sanitize(marked(marketAnalysis.value));
});

// --- Helpers ---
function formatTurnover(val) {
  if (val >= 1e8) return (val / 1e8).toFixed(2) + '亿';
  if (val >= 1e4) return (val / 1e4).toFixed(2) + '万';
  return val.toFixed(2);
}

// --- Chart functions ---
function splitData(rawData) {
  let categoryData = [], values = [], volumes = [];
  for (let i = 0; i < rawData.length; i++) {
    categoryData.push(new Date(rawData[i].timestamp * 1000).toLocaleDateString());
    values.push([rawData[i].open, rawData[i].close, rawData[i].low, rawData[i].high]);
    volumes.push([i, rawData[i].volume, rawData[i].open > rawData[i].close ? 1 : -1]);
  }
  return { categoryData, values, volumes };
}

function calculateMA(dayCount, data) {
  let result = [];
  for (let i = 0; i < data.length; i++) {
    if (i < dayCount) { result.push('-'); continue; }
    let sum = 0;
    for (let j = 0; j < dayCount; j++) sum += data[i - j][1];
    result.push((sum / dayCount).toFixed(2));
  }
  return result;
}

function processPredictionData(predictionRaw) {
  const predictionLine = [], confidenceArea = [];
  predictionRaw.forEach(p => {
    const date = new Date(p.timestamp * 1000).toLocaleDateString();
    const price = p.predicted_close_price;
    const std = p.rolling_std_7;
    predictionLine.push([date, price]);
    if (std !== null) confidenceArea.push([date, price - 1.96 * std, price + 1.96 * std]);
  });
  return { predictionLine, confidenceArea };
}

function updateChart() {
  if (!myChart.value || !allData.value.historical) return;
  const { categoryData, values } = splitData(allData.value.historical);
  const { predictionLine, confidenceArea } = processPredictionData(allData.value.prediction || []);

  const combinedCategoryData = [...categoryData];
  predictionLine.forEach(p => {
    if (!combinedCategoryData.includes(p[0])) combinedCategoryData.push(p[0]);
  });

  const series = [
    {
      name: 'Daily K', type: 'candlestick', data: values,
      itemStyle: { color: upColor, color0: downColor, borderColor: upColor, borderColor0: downColor }
    },
    { name: 'MA5', type: 'line', data: calculateMA(5, values), smooth: true, lineStyle: { opacity: 0.5 } },
    { name: 'MA10', type: 'line', data: calculateMA(10, values), smooth: true, lineStyle: { opacity: 0.5 } }
  ];

  if (showPrediction.value) {
    series.push({
      name: 'Prediction', type: 'line', data: predictionLine, smooth: true, symbol: 'none',
      lineStyle: { color: '#00ffff', width: 2, type: 'dashed' }
    });
    if (showConfidence.value) {
      series.push({
        name: 'Confidence Interval', type: 'line',
        data: confidenceArea.map(d => [d[0], d[1]]),
        lineStyle: { opacity: 0 }, stack: 'confidence', symbol: 'none'
      });
      series.push({
        name: 'Confidence Interval', type: 'line',
        data: confidenceArea.map(d => [d[0], d[2] - d[1]]),
        lineStyle: { opacity: 0 }, areaStyle: { color: 'rgba(0,255,255,0.2)' },
        stack: 'confidence', symbol: 'none'
      });
    }
  }

  myChart.value.setOption({
    backgroundColor: 'transparent',
    title: { text: '', show: false },
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' }, backgroundColor: 'rgba(0,0,0,0.9)', borderColor: '#00ff41', textStyle: { color: '#00ff41' } },
    legend: {
      data: ['Daily K', 'MA5', 'MA10', 'Prediction', 'Confidence Interval'],
      top: '4%', textStyle: { color: '#aaa', fontSize: 11 }, inactiveColor: '#444',
      selected: { 'Prediction': showPrediction.value, 'Confidence Interval': showPrediction.value && showConfidence.value }
    },
    grid: { left: '8%', right: '8%', bottom: '18%', top: '12%' },
    xAxis: {
      type: 'category', data: combinedCategoryData, scale: true, boundaryGap: false,
      axisLine: { lineStyle: { color: '#333' } }, splitLine: { show: false },
      axisLabel: { color: '#666', fontSize: 10 }
    },
    yAxis: {
      scale: true,
      splitArea: { show: true, areaStyle: { color: ['rgba(0,255,65,0.02)', 'rgba(0,255,65,0.04)'] } },
      axisLine: { lineStyle: { color: '#333' } }, axisLabel: { color: '#00ff41', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(0,255,65,0.08)' } }
    },
    dataZoom: [
      { type: 'inside', start: 70, end: 100 },
      { show: true, type: 'slider', top: '92%', start: 70, end: 100, height: 20,
        borderColor: '#333', fillerColor: 'rgba(0,255,65,0.1)', handleStyle: { color: '#00ff41' } }
    ],
    series
  });

  // Update mini chart
  updateMiniChart(allData.value.historical);
}

function updateMiniChart(hist) {
  if (!myMiniChart.value || !hist || hist.length < 2) return;
  const last7 = hist.slice(-7);
  const dates = last7.map(h => new Date(h.timestamp * 1000).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' }));
  const closes = last7.map(h => h.close);

  myMiniChart.value.setOption({
    backgroundColor: 'transparent',
    grid: { left: 0, right: 0, top: 10, bottom: 20 },
    xAxis: { type: 'category', data: dates, axisLine: { show: false }, axisLabel: { color: '#555', fontSize: 9 }, axisTick: { show: false } },
    yAxis: { show: false, scale: true },
    series: [{
      type: 'line', data: closes, smooth: true, symbol: 'circle', symbolSize: 4,
      lineStyle: { color: '#00ff41', width: 2 },
      itemStyle: { color: '#00ff41' },
      areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [
        { offset: 0, color: 'rgba(0,255,65,0.3)' }, { offset: 1, color: 'rgba(0,255,65,0)' }
      ]}}
    }]
  });
}

// --- Polling ---
async function fetchLatest() {
  try {
    const { data } = await client.get('/kline/latest', { timeout: 3000 });
    if (data.success && data.data) {
      const newLatest = data.data;
      if (!latestData.value || newLatest.timestamp !== latestData.value.timestamp) {
        prevData.value = latestData.value ? { ...latestData.value } : null;
        latestData.value = newLatest;
      }
    }
  } catch (e) { /* silent */ }
}

function startPolling() {
  pollTimer = setInterval(fetchLatest, 3000);
}

function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
}

// --- Matrix rain ---
function initMatrixRain() {
  const canvas = matrixCanvas.value;
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  const chars = 'CS2MARKETBUFFOTTE01アイウエオカキクケコ';
  const fontSize = 14;
  const columns = Math.floor(canvas.width / fontSize);
  const drops = new Array(columns).fill(1);

  function draw() {
    ctx.fillStyle = 'rgba(0,0,0,0.05)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#00ff41';
    ctx.font = fontSize + 'px monospace';
    for (let i = 0; i < drops.length; i++) {
      const text = chars[Math.floor(Math.random() * chars.length)];
      ctx.globalAlpha = Math.random() * 0.3 + 0.05;
      ctx.fillText(text, i * fontSize, drops[i] * fontSize);
      if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) drops[i] = 0;
      drops[i]++;
    }
    ctx.globalAlpha = 1;
    matrixAnimId = requestAnimationFrame(draw);
  }
  draw();
}

// --- Clock ---
function updateClock() {
  currentTime.value = new Date().toLocaleTimeString('zh-CN');
}

// --- GSAP Animations ---
function playEntryAnimations() {
  gsap.from(headerEl.value, { opacity: 0, y: -20, duration: 0.6, ease: 'power2.out' });
  gsap.from(stripEl.value, { opacity: 0, y: -10, duration: 0.5, delay: 0.2, ease: 'power2.out' });
  gsap.from(klinePanel.value, { opacity: 0, scale: 0.98, duration: 0.6, delay: 0.4, ease: 'power2.out' });
  gsap.from(bottomPanel.value, { opacity: 0, y: 20, duration: 0.5, delay: 0.6, ease: 'power2.out' });
}

// --- Lifecycle ---
onMounted(async () => {
  initMatrixRain();
  updateClock();
  setInterval(updateClock, 1000);
  playEntryAnimations();

  // Init main chart
  await nextTick();
  if (chart.value) {
    myChart.value = echarts.init(chart.value, 'dark');
    myChart.value.showLoading({ text: '加载数据...', color: '#00ff41', textColor: '#00ff41' });
  }
  if (miniChart.value) {
    myMiniChart.value = echarts.init(miniChart.value, 'dark');
  }

  // Fetch all data in parallel
  const [chartRes, analysisRes] = await Promise.all([
    client.get('/kline/chart-data'),
    client.get('/kline/market-analysis')
  ]);

  allData.value = chartRes.data;
  if (myChart.value) { myChart.value.hideLoading(); }
  updateChart();

  // Set latest/prev from historical
  if (allData.value.historical && allData.value.historical.length >= 2) {
    const hist = allData.value.historical;
    latestData.value = hist[hist.length - 1];
    prevData.value = hist[hist.length - 2];
  }

  // Market analysis
  if (analysisRes.data?.success) {
    marketAnalysis.value = analysisRes.data.analysis || '';
    analysisDate.value = analysisRes.data.date || null;
  }

  // Start polling
  fetchLatest();
  startPolling();

  // Visibility change
  document.addEventListener('visibilitychange', handleVisibility);
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  stopPolling();
  if (matrixAnimId) cancelAnimationFrame(matrixAnimId);
  if (myChart.value) myChart.value.dispose();
  if (myMiniChart.value) myMiniChart.value.dispose();
  document.removeEventListener('visibilitychange', handleVisibility);
  window.removeEventListener('resize', handleResize);
});

function handleVisibility() {
  if (document.hidden) stopPolling();
  else startPolling();
}

function handleResize() {
  myChart.value?.resize();
  myMiniChart.value?.resize();
  const canvas = matrixCanvas.value;
  if (canvas) { canvas.width = window.innerWidth; canvas.height = window.innerHeight; }
}

watch([showPrediction, showConfidence], () => {
  if (!showPrediction.value) showConfidence.value = false;
  updateChart();
});
</script>

<style scoped>
/* === Base === */
.market-page {
  width: 100%; min-height: 100vh;
  background: #000; color: #00ff41;
  font-family: 'Share Tech Mono', 'Courier New', monospace;
  position: relative; overflow-x: hidden;
  padding: 20px; box-sizing: border-box;
}
.matrix-bg { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 0; pointer-events: none; }
.scanlines {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 1; pointer-events: none;
  background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.15) 2px, rgba(0,0,0,0.15) 4px);
  animation: scanMove 8s linear infinite;
}
@keyframes scanMove { 0% { background-position: 0 0; } 100% { background-position: 0 100px; } }

.hdr, .stats-strip, .kline-panel, .bottom-grid { position: relative; z-index: 2; }

/* === Header === */
.hdr {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 20px; margin-bottom: 16px;
  border: 1px solid rgba(0,255,65,0.2); border-radius: 8px;
  background: rgba(0,0,0,0.6); backdrop-filter: blur(4px);
}
.hdr-prompt { font-size: 16px; }
.p-usr { color: #00ff41; } .p-at { color: #fff; } .p-host { color: #00ccff; }
.p-sep { color: #666; } .p-cmd { color: #fff; } .p-cur { color: #00ff41; animation: blink 1s step-end infinite; }
@keyframes blink { 50% { opacity: 0; } }
.hdr-meta { font-size: 12px; color: rgba(0,255,65,0.6); display: flex; align-items: center; gap: 6px; }
.hm-dot { width: 8px; height: 8px; border-radius: 50%; background: #00ff41; display: inline-block; }
.hm-dot.pulse { animation: pulse 1.5s ease-in-out infinite; }
@keyframes pulse { 0%,100% { opacity: 0.4; } 50% { opacity: 1; } }

/* === Stats Strip === */
.stats-strip {
  display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 16px;
}
.stat-card {
  background: rgba(0,0,0,0.5); border: 1px solid rgba(0,255,65,0.15); border-radius: 8px;
  padding: 14px 16px; text-align: center;
  transition: border-color 0.3s;
}
.stat-card:hover { border-color: rgba(0,255,65,0.4); }
.sc-label { font-size: 11px; color: rgba(0,255,65,0.5); margin-bottom: 6px; text-transform: uppercase; letter-spacing: 1px; }
.sc-value { font-size: 22px; font-weight: 700; color: #00ff41; transition: color 0.3s; }
.sc-value.up { color: #00ff41; }
.sc-value.down { color: #ff4444; }
.sc-sub { font-size: 10px; color: rgba(255,255,255,0.3); margin-top: 4px; }

/* === K-line Panel === */
.kline-panel {
  background: rgba(0,0,0,0.5); border: 1px solid rgba(0,255,65,0.2); border-radius: 8px;
  padding: 16px; margin-bottom: 16px;
}
.kline-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.kh-title { color: #00ff41; font-size: 18px; font-weight: 700; font-family: 'Share Tech Mono', monospace; }
.kline-controls { display: flex; gap: 20px; align-items: center; }
.switch-container { display: flex; align-items: center; gap: 8px; color: rgba(0,255,65,0.7); font-size: 13px; }
.switch { position: relative; display: inline-block; width: 40px; height: 20px; }
.switch input { opacity: 0; width: 0; height: 0; }
.slider { position: absolute; cursor: pointer; inset: 0; background-color: #333; transition: .3s; }
.slider:before { position: absolute; content: ""; height: 14px; width: 14px; left: 3px; bottom: 3px; background-color: #fff; transition: .3s; }
input:checked + .slider { background-color: #00ff41; }
input:disabled + .slider { background-color: #222; cursor: not-allowed; }
input:checked + .slider:before { transform: translateX(20px); }
.slider.round { border-radius: 20px; }
.slider.round:before { border-radius: 50%; }
.chart { width: 100%; height: 420px; }

/* === Bottom Grid === */
.bottom-grid {
  display: grid; grid-template-columns: 1fr 1.5fr 1fr; gap: 12px;
}
.panel-card {
  background: rgba(0,0,0,0.5); border: 1px solid rgba(0,255,65,0.15); border-radius: 8px;
  padding: 16px; display: flex; flex-direction: column;
}
.pc-hd {
  font-size: 13px; color: #00ff41; margin-bottom: 12px;
  padding-bottom: 8px; border-bottom: 1px solid rgba(0,255,65,0.1);
  display: flex; align-items: center; gap: 8px;
}
.pc-dot { width: 6px; height: 6px; border-radius: 50%; background: #00ff41; display: inline-block; }
.analysis-date { margin-left: auto; font-size: 11px; color: rgba(0,255,65,0.4); }
.mini-chart { width: 100%; height: 120px; flex: 1; }

/* Analysis card */
.analysis-body { flex: 1; overflow-y: auto; }
.analysis-text { font-size: 13px; line-height: 1.8; color: rgba(255,255,255,0.8); }
.analysis-text :deep(h1), .analysis-text :deep(h2), .analysis-text :deep(h3) { color: #00ff41; font-size: 14px; margin: 8px 0 4px; }
.analysis-text :deep(p) { margin: 4px 0; }
.analysis-text :deep(strong) { color: #00ff41; }
.analysis-empty { flex: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; color: rgba(0,255,65,0.3); gap: 8px; }
.empty-icon { font-size: 32px; opacity: 0.5; }

/* Data metrics */
.data-rows { display: flex; flex-direction: column; gap: 8px; }
.dr { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid rgba(0,255,65,0.06); }
.dr:last-child { border-bottom: none; }
.dr-k { color: rgba(0,255,65,0.5); font-size: 12px; }
.dr-v { color: rgba(255,255,255,0.8); font-size: 13px; font-weight: 600; }
.dr-v.up { color: #00ff41; }
.dr-v.down { color: #ff4444; }

/* === Responsive === */
@media (max-width: 900px) {
  .stats-strip { grid-template-columns: repeat(3, 1fr); }
  .bottom-grid { grid-template-columns: 1fr; }
}
@media (max-width: 600px) {
  .stats-strip { grid-template-columns: repeat(2, 1fr); }
  .chart { height: 300px; }
}
</style>
