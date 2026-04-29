<template>
  <div ref="rootEl" class="items-page">
    <!-- Matrix rain canvas -->
    <canvas ref="matrixCanvas" class="matrix-bg" aria-hidden="true"></canvas>
    <!-- Scanlines overlay -->
    <div class="scanlines" aria-hidden="true"></div>

    <!-- HEADER -->
    <header ref="headerEl" class="hdr">
      <div class="hdr-prompt">
        <span class="p-usr">root</span><span class="p-at">@</span
        ><span class="p-host">buffotte</span><span class="p-sep">:~#&nbsp;</span
        ><span ref="typedEl" class="p-cmd"></span><span class="p-cur">█</span>
      </div>
      <div class="hdr-meta">
        <span class="hm-dot"></span>
        ITEM SCANNER &nbsp;·&nbsp; CS2 SKIN INTELLIGENCE
      </div>
    </header>

    <!-- MAIN LAYOUT -->
    <div class="main-grid">
      <!-- LEFT: Search Panel -->
      <div ref="searchPanelEl" class="panel-card search-panel">
        <div class="pc-hd">
          <span class="pc-dot"></span>饰品搜索
          <span v-if="searchResults.length" class="result-count">{{
            searchResults.length
          }}</span>
        </div>
        <div class="search-box">
          <input
            v-model="searchQuery"
            @input="handleSearch"
            type="text"
            placeholder="输入饰品名称 (支持中英文)..."
            class="search-input"
          />
          <div v-if="searching" class="search-loading">
            <span class="spin-dot"></span>
          </div>
        </div>

        <!-- Search Results -->
        <div v-if="searchResults.length > 0" class="results-list">
          <div
            v-for="(item, idx) in searchResults"
            :key="item.id"
            class="result-item"
            :class="{ selected: selectedItem?.id === item.id }"
            @click="selectItem(item)"
            :ref="(el) => { if (el) resultItemRefs[idx] = el }"
          >
            <div class="ri-name">{{ item.name }}</div>
            <div class="ri-hash">{{ item.market_hash_name }}</div>
          </div>
        </div>

        <!-- Empty States -->
        <div
          v-if="!searchResults.length && !searching && searchQuery"
          class="panel-empty"
        >
          <div class="empty-line">// 未找到匹配的饰品</div>
        </div>
        <div v-if="!searchQuery && !selectedItem" class="panel-empty">
          <div class="empty-line">> 输入饰品名称开始搜索</div>
        </div>
      </div>

      <!-- RIGHT: Content Area -->
      <div class="content-area">
        <!-- Item Info Bar -->
        <div
          ref="infoBarEl"
          class="panel-card info-bar"
          v-if="selectedItem && priceData"
        >
          <div class="info-left">
            <div class="info-name">{{ selectedItem.name }}</div>
            <div class="info-time">
              更新: {{ formatTime(priceData.updateTime) }}
            </div>
          </div>
          <button
            class="track-btn"
            @click="trackItem(selectedItem.market_hash_name)"
          >
            <span class="tb-icon">+</span> 追踪此饰品
          </button>
        </div>

        <!-- Price Strip -->
        <div
          ref="priceStripEl"
          class="price-strip"
          v-if="selectedItem && priceData"
        >
          <div
            class="price-card"
            v-for="(platform, index) in displayPlatforms"
            :key="index"
            :class="{ empty: platform.platform === '-' }"
          >
            <div class="pf-name">{{ platform.platform }}</div>
            <div class="pf-body" v-if="platform.platform !== '-'">
              <div class="pf-row">
                <span class="pf-label">卖</span>
                <span
                  class="pf-val"
                  :class="{
                    'highlight-sell-low': isPriceExtreme(platform.sellPrice, lowestSellPrice),
                    'highlight-sell-high': isPriceExtreme(platform.sellPrice, highestSellPrice),
                  }"
                  >¥{{ platform.sellPrice }}</span
                >
                <span class="pf-cnt">({{ platform.sellCount }})</span>
              </div>
              <div class="pf-row">
                <span class="pf-label">购</span>
                <span
                  class="pf-val"
                  :class="{
                    'highlight-bid-low': isPriceExtreme(platform.biddingPrice, lowestBiddingPrice),
                    'highlight-bid-high': isPriceExtreme(platform.biddingPrice, highestBiddingPrice),
                  }"
                  >¥{{ platform.biddingPrice }}</span
                >
                <span class="pf-cnt">({{ platform.biddingCount }})</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Loading State for Price -->
        <div
          v-if="loadingPrice"
          class="panel-card panel-loading"
        >
          <div class="ld-spinner"></div>
          <span>正在获取价格数据...</span>
        </div>

        <!-- K-line Chart -->
        <div ref="klinePanelEl" class="panel-card chart-panel">
          <div class="pc-hd">
            <span class="pc-dot"></span>K线走势
          </div>
          <div
            v-if="klineData.length > 0"
            ref="klineChart"
            class="chart-container"
          ></div>
          <div v-if="loadingKlineData" class="panel-loading-inline">
            <div class="ld-spinner sm"></div>
            <span>正在获取K线数据...</span>
          </div>
          <div v-else-if="klineError" class="panel-empty">
            <div class="empty-line error">{{ klineError }}</div>
          </div>
          <div
            v-else-if="!loadingKlineData && !klineData.length && selectedItem"
            class="panel-empty"
          >
            <div class="empty-line">暂无K线数据</div>
          </div>
          <div v-else-if="!selectedItem" class="panel-empty">
            <div class="empty-line">> 选择饰品查看K线走势</div>
          </div>
        </div>

        <!-- Data Charts -->
        <div ref="dataPanelEl" class="panel-card chart-panel">
          <div class="pc-hd">
            <span class="pc-dot"></span>成交量分析
          </div>
          <div
            v-if="klineData.length > 0"
            ref="dataChart"
            class="chart-container"
          ></div>
          <div v-if="loadingKlineData" class="panel-loading-inline">
            <div class="ld-spinner sm"></div>
            <span>正在加载数据...</span>
          </div>
          <div v-else-if="klineError" class="panel-empty">
            <div class="empty-line error">{{ klineError }}</div>
          </div>
          <div
            v-else-if="!loadingKlineData && !klineData.length && selectedItem"
            class="panel-empty"
          >
            <div class="empty-line">暂无数据</div>
          </div>
          <div v-else-if="!selectedItem" class="panel-empty">
            <div class="empty-line">> 选择饰品查看数据图表</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, shallowRef, reactive, computed, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { useRoute } from 'vue-router';
import api, { client } from '../services/api';
import * as echarts from 'echarts/core';
import { useToast } from '../composables/useToast';
import {
  TitleComponent, TooltipComponent, LegendComponent, GridComponent,
  DataZoomComponent, MarkPointComponent, MarkLineComponent,
} from 'echarts/components';
import { CandlestickChart, LineChart, BarChart } from 'echarts/charts';
import { CanvasRenderer } from 'echarts/renderers';
import gsap from 'gsap';

echarts.use([
  TitleComponent, TooltipComponent, LegendComponent, GridComponent,
  DataZoomComponent, MarkPointComponent, MarkLineComponent,
  CandlestickChart, LineChart, BarChart, CanvasRenderer,
]);

const route = useRoute();
const toast = useToast();

// DOM refs
const rootEl = ref(null);
const matrixCanvas = ref(null);
const headerEl = ref(null);
const typedEl = ref(null);
const searchPanelEl = ref(null);
const infoBarEl = ref(null);
const priceStripEl = ref(null);
const klinePanelEl = ref(null);
const dataPanelEl = ref(null);
const klineChart = ref(null);
const dataChart = ref(null);
const resultItemRefs = reactive({});

// Chart instances
const myKlineChart = shallowRef(null);
const myDataChart = shallowRef(null);

// State
const searchQuery = ref('');
const searchResults = ref([]);
const selectedItem = ref(null);
const priceData = ref(null);
const searching = ref(false);
const loadingPrice = ref(false);
const klineData = ref([]);
const loadingKlineData = ref(false);
const klineError = ref(null);
const lowestSellPrice = ref(null);
const highestSellPrice = ref(null);
const lowestBiddingPrice = ref(null);
const highestBiddingPrice = ref(null);
const user = ref(JSON.parse(localStorage.getItem('user')));
let searchTimeout = null;

// Matrix rain
let _raf = null;
let _matrixCleanup = null;

// GSAP context
let _ctx = null;

// Colors
const upColor = '#00ff00';
const downColor = '#ff0000';

// Computed: display platforms (always show 10 slots)
const displayPlatforms = computed(() => {
  if (!priceData.value) return [];
  return Array(10).fill(null).map((_, i) =>
    priceData.value.data[i] || {
      platform: '-', sellPrice: '-', sellCount: '-',
      biddingPrice: '-', biddingCount: '-',
    }
  );
});

const isPriceExtreme = (value, extreme) => {
  const price = Number(value);
  return extreme !== null && Number.isFinite(price) && price > 0 && price === extreme;
};

// --- Matrix rain background ---
const initMatrix = () => {
  const c = matrixCanvas.value;
  if (!c) return;
  const ctx = c.getContext('2d');
  const FS = 13;
  const JP = 'ｦｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈ0123456789ABCDEF@#$%';
  let cols, drops;
  const resize = () => {
    c.width = window.innerWidth;
    c.height = window.innerHeight;
    cols = Math.ceil(c.width / FS);
    drops = Array.from({ length: cols }, () => -(Math.random() * (c.height / FS)));
  };
  resize();
  window.addEventListener('resize', resize);
  const draw = () => {
    ctx.fillStyle = 'rgba(0,0,0,0.05)';
    ctx.fillRect(0, 0, c.width, c.height);
    ctx.font = `${FS}px monospace`;
    for (let i = 0; i < cols; i++) {
      const ch = JP[Math.floor(Math.random() * JP.length)];
      const y = drops[i] * FS;
      ctx.fillStyle = drops[i] < 2
        ? 'rgba(200,255,200,0.8)'
        : `rgba(0,255,65,${Math.random() * 0.18 + 0.03})`;
      ctx.fillText(ch, i * FS, y);
      if (y > c.height && Math.random() > 0.975) drops[i] = 0;
      drops[i] += 0.35;
    }
    _raf = requestAnimationFrame(draw);
  };
  draw();
  _matrixCleanup = () => {
    window.removeEventListener('resize', resize);
    if (_raf) cancelAnimationFrame(_raf);
  };
};

// --- Typewriter ---
const typewriter = async (el, text, msBase = 42) => {
  el.textContent = '';
  for (const ch of text) {
    el.textContent += ch;
    await new Promise((r) => setTimeout(r, msBase + Math.random() * 22));
  }
};

// --- GSAP entrance animations ---
const initGSAP = () => {
  _ctx = gsap.context(() => {
    const tl = gsap.timeline({ delay: 0.05 });

    tl.fromTo(headerEl.value,
      { opacity: 0, y: -28 },
      { opacity: 1, y: 0, duration: 0.55, ease: 'power2.out' }
    );

    tl.fromTo(searchPanelEl.value,
      { opacity: 0, x: -36 },
      { opacity: 1, x: 0, duration: 0.5, ease: 'power2.out' },
      '-=0.2'
    );

    tl.fromTo([klinePanelEl.value, dataPanelEl.value],
      { opacity: 0, y: 30 },
      { opacity: 1, y: 0, duration: 0.55, stagger: 0.12, ease: 'power3.out' },
      '-=0.15'
    );

    // Glow pulse on panel headers
    gsap.to('.pc-dot', {
      boxShadow: '0 0 10px #00ff41, 0 0 20px rgba(0,255,65,0.4)',
      duration: 1.8,
      yoyo: true,
      repeat: -1,
      stagger: { each: 0.6, from: 'random' },
      ease: 'sine.inOut',
    });
  }, rootEl.value);
};

// Animate price cards entrance
const animatePriceCards = () => {
  if (!priceStripEl.value) return;
  const cards = priceStripEl.value.querySelectorAll('.price-card');
  gsap.fromTo(cards,
    { opacity: 0, y: 16, scale: 0.95 },
    { opacity: 1, y: 0, scale: 1, duration: 0.4, stagger: 0.04, ease: 'power2.out' }
  );
};

// Animate info bar
const animateInfoBar = () => {
  if (!infoBarEl.value) return;
  gsap.fromTo(infoBarEl.value,
    { opacity: 0, y: -16 },
    { opacity: 1, y: 0, duration: 0.4, ease: 'power2.out' }
  );
};

// --- Track item ---
const trackItem = async (marketHashName) => {
  if (!user.value) {
    toast.error('请先登录再追踪饰品。');
    return;
  }
  try {
    const result = await client.post('/track/add', {
      email: user.value.email,
      market_hash_name: marketHashName,
    }, { timeout: 15000 });
    if (result.data.success) {
      toast.success('饰品已成功追踪！');
    } else {
      toast.error(`追踪失败: ${result.data.message}`);
    }
  } catch (error) {
    if (error.code === 'ECONNABORTED' || error.code === 'ERR_CANCELED') {
      toast.success('饰品已成功追踪！');
    } else {
      toast.error('追踪饰品时出错，请查看控制台获取更多信息。');
    }
  }
};

// --- Search ---
const handleSearch = () => {
  if (searchTimeout) clearTimeout(searchTimeout);
  if (!searchQuery.value.trim()) {
    searchResults.value = [];
    return;
  }
  searchTimeout = setTimeout(async () => {
    searching.value = true;
    try {
      const result = await api.searchItems(searchQuery.value);
      if (result.success) {
        searchResults.value = result.data || [];
        // Animate results entrance
        await nextTick();
        const items = Object.values(resultItemRefs);
        if (items.length) {
          gsap.fromTo(items,
            { opacity: 0, x: -12 },
            { opacity: 1, x: 0, duration: 0.3, stagger: 0.04, ease: 'power2.out' }
          );
        }
      }
    } catch (error) {
      console.error('搜索失败:', error);
    } finally {
      searching.value = false;
    }
  }, 300);
};

// --- Select item ---
const selectItem = async (item) => {
  selectedItem.value = item;
  priceData.value = null;
  klineData.value = [];
  klineError.value = null;
  loadingPrice.value = true;
  loadingKlineData.value = true;
  lowestSellPrice.value = null;
  highestSellPrice.value = null;
  lowestBiddingPrice.value = null;
  highestBiddingPrice.value = null;

  try {
    const priceResult = await api.getItemPrice(item.market_hash_name);
    if (priceResult.success) {
      priceData.value = {
        data: priceResult.data,
        updateTime: priceResult.data[0]?.updateTime || Date.now() / 1000,
      };
      let minSell = Infinity;
      let maxSell = -Infinity;
      let minBidding = Infinity;
      let maxBidding = -Infinity;
      priceResult.data.forEach((p) => {
        const sellPrice = Number(p.sellPrice);
        const biddingPrice = Number(p.biddingPrice);
        if (Number.isFinite(sellPrice) && sellPrice > 0 && sellPrice < minSell) minSell = sellPrice;
        if (Number.isFinite(sellPrice) && sellPrice > 0 && sellPrice > maxSell) maxSell = sellPrice;
        if (Number.isFinite(biddingPrice) && biddingPrice > 0 && biddingPrice < minBidding) minBidding = biddingPrice;
        if (Number.isFinite(biddingPrice) && biddingPrice > 0 && biddingPrice > maxBidding) maxBidding = biddingPrice;
      });
      lowestSellPrice.value = minSell !== Infinity ? minSell : null;
      highestSellPrice.value = maxSell !== -Infinity ? maxSell : null;
      lowestBiddingPrice.value = minBidding !== Infinity ? minBidding : null;
      highestBiddingPrice.value = maxBidding !== -Infinity ? maxBidding : null;
      await nextTick();
      animateInfoBar();
      animatePriceCards();
    }
  } catch (error) {
    console.error('获取价格失败:', error);
  } finally {
    loadingPrice.value = false;
  }

  try {
    const klineResult = await api.getItemKlineData(item.market_hash_name);
    if (klineResult.success) {
      klineData.value = klineResult.data || [];
      klineError.value = null;
    } else {
      klineError.value = klineResult.error?.status === 404
        ? '该饰品暂不支持K线查询'
        : (klineResult.error?.message || '获取K线数据失败');
    }
  } catch (error) {
    klineError.value = '获取K线数据失败，请稍后重试';
  } finally {
    loadingKlineData.value = false;
  }
};

// --- Time formatting ---
const formatTime = (timestamp) => {
  if (!timestamp) return '';
  return new Date(timestamp * 1000).toLocaleString('zh-CN');
};

// --- ECharts data processing ---
function splitData(rawData) {
  let categoryData = [], candlestickData = [], totalCountData = [];
  let buyCountData = [], sellCountData = [], turnoverData = [], volumeData = [];

  if (!rawData || rawData.length === 0) return {
    categoryData, candlestickData, totalCountData, buyCountData, sellCountData, turnoverData, volumeData,
  };

  for (let i = 0; i < rawData.length; i++) {
    const item = rawData[i];
    if (!item || item.timestamp === undefined) continue;

    const price = parseFloat(item.price);
    const buyPrice = parseFloat(item.buy_price);
    const open = buyPrice;
    const close = price;
    const low = Math.min(price, buyPrice);
    const high = Math.max(price, buyPrice);

    categoryData.push(new Date(item.timestamp * 1000).toLocaleDateString('zh-CN'));
    candlestickData.push([open, close, low, high]);
    totalCountData.push(parseInt(item.total_count));
    buyCountData.push(parseInt(item.buy_count));
    sellCountData.push(parseInt(item.sell_count));
    turnoverData.push(parseFloat(item.turnover));
    volumeData.push(parseInt(item.volume));
  }
  return { categoryData, candlestickData, totalCountData, buyCountData, sellCountData, turnoverData, volumeData };
}

// --- K-line chart option ---
const klineChartOption = {
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'cross' },
    backgroundColor: 'rgba(0,0,0,0.9)',
    borderColor: '#00ff41',
    textStyle: { color: '#00ff41' },
    formatter(params) {
      if (!params?.length) return '';
      let res = `日期: ${params[0].name}<br/>`;
      params.forEach((p) => {
        if (p.seriesName === 'Daily Price' && p.data !== undefined)
          res += `在售最低价: ${p.data.toFixed(2)}<br/>`;
        else if (p.seriesName === 'Buy Price' && p.data !== undefined)
          res += `求购最高价: ${p.data.toFixed(2)}<br/>`;
        else if (p.seriesName === '交易个数' && p.data !== undefined)
          res += `交易个数: ${p.data}<br/>`;
      });
      return res;
    },
  },
  legend: {
    data: ['Daily Price', 'Buy Price', '交易个数'],
    top: '4%',
    textStyle: { color: '#aaa', fontSize: 11 },
    inactiveColor: '#555',
  },
  grid: { left: '8%', right: '8%', bottom: '18%', top: '14%' },
  xAxis: {
    type: 'category', scale: true, boundaryGap: false,
    axisLine: { lineStyle: { color: '#333' } }, splitLine: { show: false },
    axisLabel: {
      color: '#666', fontSize: 10,
      formatter: (v) => { const d = new Date(v); return `${d.getMonth() + 1}/${d.getDate()}`; },
    },
  },
  yAxis: [
    {
      scale: true, position: 'left',
      axisLine: { lineStyle: { color: '#00ff41' } },
      splitLine: { lineStyle: { color: 'rgba(0,255,65,0.08)' } },
      axisLabel: { color: '#00ff41', fontSize: 10 },
      splitArea: { show: true, areaStyle: { color: ['rgba(0,255,65,0.02)', 'rgba(0,255,65,0.04)'] } },
    },
    {
      scale: true, position: 'right', alignTicks: true,
      axisLine: { lineStyle: { color: '#ADFF2F' } },
      axisLabel: { color: '#ADFF2F', fontSize: 10 },
    },
  ],
  dataZoom: [
    { type: 'inside', start: 70, end: 100 },
    {
      show: true, type: 'slider', top: '92%', start: 70, end: 100, height: 20,
      borderColor: '#333', fillerColor: 'rgba(0,255,65,0.1)', handleStyle: { color: '#00ff41' },
    },
  ],
  series: [],
};

// --- Init K-line chart ---
const initKlineChart = async () => {
  if (!klineData.value?.length) return;
  await nextTick();
  if (!klineChart.value) return;
  if (myKlineChart.value) myKlineChart.value.dispose();
  myKlineChart.value = echarts.init(klineChart.value, 'dark');
  updateKlineChart();
};

// --- Update K-line chart ---
const updateKlineChart = () => {
  if (!myKlineChart.value || !klineData.value.length) {
    myKlineChart.value?.clear();
    return;
  }
  const { categoryData, candlestickData, volumeData, totalCountData, buyCountData, sellCountData, turnoverData } = splitData(klineData.value);

  myKlineChart.value.setOption({
    ...klineChartOption,
    xAxis: { ...klineChartOption.xAxis, data: categoryData },
    series: [
      {
        name: 'Daily Price', type: 'line',
        data: candlestickData.map((d) => d[1]),
        smooth: true, showSymbol: false,
        lineStyle: { opacity: 0.8, width: 2, color: upColor },
        itemStyle: { color: upColor },
        areaStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(0,255,0,0.15)' },
              { offset: 1, color: 'rgba(0,255,0,0)' },
            ],
          },
        },
      },
      {
        name: 'Buy Price', type: 'line',
        data: candlestickData.map((d) => d[0]),
        smooth: true, showSymbol: false,
        lineStyle: { opacity: 0.8, width: 2, color: downColor },
        itemStyle: { color: downColor },
        areaStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(255,0,0,0.08)' },
              { offset: 1, color: 'rgba(255,0,0,0)' },
            ],
          },
        },
      },
      {
        name: '交易个数', type: 'bar', data: volumeData, yAxisIndex: 1,
        itemStyle: { color: '#ADFF2F', opacity: 0.4 },
      },
    ],
  });

  updateDataChart(categoryData, totalCountData, buyCountData, sellCountData, turnoverData, volumeData);
};

// --- Init data chart ---
const initDataChart = async () => {
  if (!klineData.value?.length) return;
  await nextTick();
  if (!dataChart.value) return;
  if (myDataChart.value) myDataChart.value.dispose();
  myDataChart.value = echarts.init(dataChart.value, 'dark');
  updateDataChart();
};

// --- Update data chart ---
const updateDataChart = (categoryData, totalCountData, buyCountData, sellCountData, turnoverData, volumeData) => {
  if (!myDataChart.value) return;
  if (!categoryData) {
    if (!klineData.value.length) { myDataChart.value?.clear(); return; }
    const data = splitData(klineData.value);
    categoryData = data.categoryData;
    totalCountData = data.totalCountData;
    buyCountData = data.buyCountData;
    sellCountData = data.sellCountData;
    turnoverData = data.turnoverData;
    volumeData = data.volumeData;
  }

  myDataChart.value.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis', axisPointer: { type: 'cross' },
      backgroundColor: 'rgba(0,0,0,0.9)', borderColor: '#00ff41', textStyle: { color: '#00ff41' },
    },
    legend: {
      data: ['存世量', '求购数量', '在售数量', '交易额'],
      top: '4%', textStyle: { color: '#aaa', fontSize: 11 }, inactiveColor: '#555',
    },
    grid: { left: '8%', right: '8%', bottom: '18%', top: '14%' },
    dataZoom: [
      { type: 'inside', start: 70, end: 100 },
      {
        show: true, type: 'slider', top: '92%', start: 70, end: 100, height: 20,
        borderColor: '#333', fillerColor: 'rgba(0,255,65,0.1)', handleStyle: { color: '#00ff41' },
      },
    ],
    xAxis: {
      type: 'category', data: categoryData,
      axisLine: { lineStyle: { color: '#333' } },
      axisLabel: {
        color: '#666', fontSize: 10,
        formatter: (v) => { const d = new Date(v); return `${d.getMonth() + 1}/${d.getDate()}`; },
      },
    },
    yAxis: [
      {
        type: 'value', name: '存世量', position: 'left', alignTicks: true,
        axisLine: { lineStyle: { color: '#8A2BE2' } }, axisLabel: { color: '#8A2BE2', fontSize: 10 },
      },
      {
        type: 'value', name: '买卖数量', position: 'right', alignTicks: true,
        axisLine: { lineStyle: { color: '#00BFFF' } }, axisLabel: { color: '#00BFFF', fontSize: 10 },
      },
      {
        type: 'value', name: '交易额', position: 'right', offset: 60, alignTicks: true,
        axisLine: { lineStyle: { color: '#FFA500' } }, axisLabel: { color: '#FFA500', fontSize: 10 },
      },
    ],
    series: [
      {
        name: '存世量', type: 'line', data: totalCountData, yAxisIndex: 0,
        smooth: true, showSymbol: false,
        lineStyle: { color: '#8A2BE2', width: 2 },
        areaStyle: {
          color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [
            { offset: 0, color: 'rgba(138,43,226,0.15)' }, { offset: 1, color: 'rgba(138,43,226,0)' },
          ]},
        },
      },
      {
        name: '求购数量', type: 'line', data: buyCountData, yAxisIndex: 1,
        smooth: true, showSymbol: false,
        lineStyle: { color: '#00BFFF', width: 2 },
      },
      {
        name: '在售数量', type: 'line', data: sellCountData, yAxisIndex: 1,
        smooth: true, showSymbol: false,
        lineStyle: { color: '#FFD700', width: 2 },
      },
      {
        name: '交易额', type: 'bar', data: turnoverData, yAxisIndex: 2,
        itemStyle: { color: '#FFA500', opacity: 0.5 },
      },
    ],
  });
};

// --- Watch kline data ---
watch(klineData, async (newVal) => {
  await nextTick();
  if (myKlineChart.value) { myKlineChart.value.dispose(); myKlineChart.value = null; }
  if (myDataChart.value) { myDataChart.value.dispose(); myDataChart.value = null; }
  if (newVal?.length > 0) {
    initKlineChart();
    initDataChart();
  }
}, { immediate: true });

// --- Lifecycle ---
onMounted(async () => {
  initMatrix();
  initGSAP();

  // Typewriter header
  setTimeout(async () => {
    if (!typedEl.value) return;
    await typewriter(typedEl.value, './item-search.sh --mode=scan', 42);
  }, 300);

  // Support URL query auto-search
  const q = route.query.search;
  if (q) {
    searchQuery.value = q;
    searching.value = true;
    try {
      const result = await api.searchItems(q);
      if (result.success) searchResults.value = result.data || [];
    } catch (error) {
      console.error('自动搜索失败:', error);
    } finally {
      searching.value = false;
    }
  }

  // Handle resize for charts
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  if (_matrixCleanup) _matrixCleanup();
  if (_ctx) _ctx.revert();
  if (myKlineChart.value) myKlineChart.value.dispose();
  if (myDataChart.value) myDataChart.value.dispose();
  window.removeEventListener('resize', handleResize);
});

const handleResize = () => {
  myKlineChart.value?.resize();
  myDataChart.value?.resize();
  const c = matrixCanvas.value;
  if (c) { c.width = window.innerWidth; c.height = window.innerHeight; }
};
</script>

<style scoped>
/* === Base === */
.items-page {
  width: 100%;
  min-height: 100vh;
  position: relative;
  padding: 20px;
  font-family: 'Share Tech Mono', 'Source Code Pro', monospace;
}

/* Matrix canvas */
.matrix-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  opacity: 0.35;
}

/* Scanlines */
.scanlines {
  position: fixed;
  inset: 0;
  z-index: 9990;
  pointer-events: none;
  background: repeating-linear-gradient(
    0deg, transparent, transparent 2px,
    rgba(0, 0, 0, 0.04) 2px, rgba(0, 0, 0, 0.04) 4px
  );
  animation: scanmove 12s linear infinite;
}
@keyframes scanmove {
  from { background-position: 0 0; }
  to { background-position: 0 100vh; }
}

/* === Header === */
.hdr {
  position: relative;
  z-index: 2;
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(0, 255, 65, 0.18);
}
.hdr-prompt {
  font-size: 18px;
  font-weight: 700;
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  line-height: 1.7;
}
.p-usr { color: #00e5ff; text-shadow: 0 0 8px rgba(0, 229, 255, 0.5); }
.p-at { color: rgba(0, 255, 65, 0.6); }
.p-host { color: var(--primary-green); text-shadow: 0 0 8px rgba(0, 255, 65, 0.5); }
.p-sep { color: rgba(0, 255, 65, 0.45); }
.p-cmd { color: var(--primary-green); min-width: 2ch; }
.p-cur { color: var(--primary-green); animation: blink 1s step-end infinite; margin-left: 1px; }
@keyframes blink { 50% { opacity: 0; } }

.hdr-meta {
  margin-top: 6px;
  font-size: 12px;
  color: rgba(0, 255, 65, 0.5);
  letter-spacing: 1.2px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.hm-dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #00ff41;
  box-shadow: 0 0 8px #00ff41;
  animation: pdot 2s ease-in-out infinite;
}
@keyframes pdot {
  0%, 100% { box-shadow: 0 0 4px #00ff41; }
  50% { box-shadow: 0 0 14px #00ff41, 0 0 28px rgba(0, 255, 65, 0.35); }
}

/* === Main Grid Layout === */
.main-grid {
  position: relative;
  z-index: 2;
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 16px;
}
@media (max-width: 900px) {
  .main-grid {
    grid-template-columns: 1fr;
  }
}

/* === Panel Card (shared) === */
.panel-card {
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(0, 255, 65, 0.15);
  border-radius: 8px;
  overflow: hidden;
  backdrop-filter: blur(8px);
  transition: border-color 0.3s, box-shadow 0.3s;
}
.panel-card:hover {
  border-color: rgba(0, 255, 65, 0.3);
  box-shadow: 0 4px 20px rgba(0, 255, 65, 0.06);
}

.pc-hd {
  font-size: 13px;
  color: var(--primary-green);
  padding: 10px 14px;
  border-bottom: 1px solid rgba(0, 255, 65, 0.08);
  background: rgba(0, 255, 65, 0.025);
  display: flex;
  align-items: center;
  gap: 8px;
  letter-spacing: 0.5px;
  font-weight: 600;
}
.pc-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--primary-green);
  box-shadow: 0 0 6px var(--primary-green);
  flex-shrink: 0;
}

/* === Search Panel === */
.search-panel {
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 120px);
  position: sticky;
  top: 20px;
}

.search-box {
  position: relative;
  padding: 10px 12px;
}
.search-input {
  width: 100%;
  padding: 9px 36px 9px 12px;
  font-size: 13px;
  font-family: 'Share Tech Mono', monospace;
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(0, 255, 65, 0.2);
  border-radius: 6px;
  color: var(--primary-green);
  outline: none;
  transition: border-color 0.3s, box-shadow 0.3s;
}
.search-input::placeholder { color: rgba(0, 255, 65, 0.35); }
.search-input:focus {
  border-color: rgba(0, 255, 65, 0.5);
  box-shadow: 0 0 16px rgba(0, 255, 65, 0.15);
}

.search-loading {
  position: absolute;
  right: 22px;
  top: 50%;
  transform: translateY(-50%);
}
.spin-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--primary-green);
  animation: spin-pulse 0.8s ease-in-out infinite;
}
@keyframes spin-pulse {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1.2); }
}

/* Result count badge */
.result-count {
  margin-left: auto;
  font-size: 10px;
  padding: 1px 7px;
  border-radius: 3px;
  letter-spacing: 1px;
  border: 1px solid rgba(0, 255, 65, 0.35);
  background: rgba(0, 255, 65, 0.07);
  color: var(--primary-green);
}

/* Results list */
.results-list {
  flex: 1;
  overflow-y: auto;
}
.results-list::-webkit-scrollbar { width: 4px; }
.results-list::-webkit-scrollbar-track { background: transparent; }
.results-list::-webkit-scrollbar-thumb { background: rgba(0, 255, 65, 0.25); border-radius: 2px; }
.results-list::-webkit-scrollbar-thumb:hover { background: rgba(0, 255, 65, 0.4); }

.result-item {
  padding: 10px 14px;
  cursor: pointer;
  border-bottom: 1px solid rgba(0, 255, 65, 0.06);
  transition: background 0.2s, border-color 0.2s;
}
.result-item:hover {
  background: rgba(0, 255, 65, 0.05);
}
.result-item.selected {
  background: rgba(0, 255, 65, 0.1);
  border-left: 2px solid var(--primary-green);
}
.ri-name {
  font-size: 13px;
  color: var(--primary-green);
  font-weight: 500;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.ri-hash {
  font-size: 10px;
  color: rgba(0, 255, 65, 0.45);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Empty state */
.panel-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 16px;
  flex-grow: 1;
}
.empty-line {
  font-size: 13px;
  color: rgba(0, 255, 65, 0.35);
  font-family: 'Share Tech Mono', monospace;
}
.empty-line.error { color: rgba(255, 80, 80, 0.7); }

/* === Content Area === */
.content-area {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}

/* Info bar */
.info-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  gap: 12px;
}
.info-left {
  display: flex;
  align-items: baseline;
  gap: 12px;
  min-width: 0;
}
.info-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--primary-green);
  text-shadow: 0 0 8px rgba(0, 255, 65, 0.3);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.info-time {
  font-size: 11px;
  color: rgba(0, 255, 65, 0.45);
  white-space: nowrap;
}

/* Track button */
.track-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 16px;
  background: rgba(0, 255, 65, 0.08);
  border: 1px solid rgba(0, 255, 65, 0.3);
  border-radius: 5px;
  color: var(--primary-green);
  font-family: 'Share Tech Mono', monospace;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.25s ease;
  letter-spacing: 0.5px;
}
.track-btn:hover {
  background: rgba(0, 255, 65, 0.15);
  border-color: rgba(0, 255, 65, 0.5);
  box-shadow: 0 0 16px rgba(0, 255, 65, 0.15);
  transform: translateY(-1px);
}
.tb-icon {
  font-size: 14px;
  font-weight: 700;
}

/* === Price Strip === */
.price-strip {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 8px;
}
@media (max-width: 1100px) {
  .price-strip { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 600px) {
  .price-strip { grid-template-columns: repeat(2, 1fr); }
}

.price-card {
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(0, 255, 65, 0.12);
  border-radius: 6px;
  padding: 8px 10px;
  transition: border-color 0.3s, box-shadow 0.3s, transform 0.2s;
}
.price-card:hover {
  border-color: rgba(0, 255, 65, 0.35);
  box-shadow: 0 0 12px rgba(0, 255, 65, 0.08);
  transform: translateY(-2px);
}
.price-card.empty {
  background: rgba(0, 0, 0, 0.2);
  border: 1px dashed rgba(0, 255, 65, 0.08);
}
.pf-name {
  font-size: 11px;
  color: rgba(0, 255, 65, 0.6);
  font-weight: 700;
  text-align: center;
  margin-bottom: 6px;
  letter-spacing: 0.5px;
}
.pf-body { display: flex; flex-direction: column; gap: 3px; }
.pf-row {
  display: flex;
  align-items: center;
  gap: 4px;
}
.pf-label {
  font-size: 10px;
  color: rgba(0, 255, 65, 0.4);
  width: 16px;
  flex-shrink: 0;
}
.pf-val {
  font-size: 13px;
  font-weight: 700;
  color: var(--primary-green);
  transition: color 0.3s, text-shadow 0.3s;
}
.pf-cnt {
  font-size: 9px;
  color: rgba(0, 255, 65, 0.35);
}
.pf-val.highlight-sell-low {
  color: #00e5ff !important;
  text-shadow: 0 0 8px rgba(0, 229, 255, 0.6);
}
.pf-val.highlight-sell-high {
  color: #ff4444 !important;
  text-shadow: 0 0 8px rgba(255, 68, 68, 0.6);
}
.pf-val.highlight-bid-low {
  color: #ffdd00 !important;
  text-shadow: 0 0 8px rgba(255, 221, 0, 0.6);
}
.pf-val.highlight-bid-high {
  color: #00ff41 !important;
  text-shadow: 0 0 8px rgba(0, 255, 65, 0.65);
}

/* === Chart Panels === */
.chart-panel {
  min-height: 380px;
  display: flex;
  flex-direction: column;
}
.chart-container {
  flex: 1;
  width: 100%;
  min-height: 350px;
}

/* Loading states */
.panel-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 24px;
  color: rgba(0, 255, 65, 0.5);
  font-size: 13px;
}
.panel-loading-inline {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 40px;
  color: rgba(0, 255, 65, 0.5);
  font-size: 13px;
  flex-grow: 1;
}
.ld-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(0, 255, 65, 0.15);
  border-top-color: var(--primary-green);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
.ld-spinner.sm { width: 14px; height: 14px; border-width: 2px; }
@keyframes spin { to { transform: rotate(360deg); } }

/* === Responsive === */
@media (max-width: 900px) {
  .items-page { padding: 16px 12px; }
  .search-panel {
    position: static;
    max-height: 360px;
  }
  .info-bar {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
