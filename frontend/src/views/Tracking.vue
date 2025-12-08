<template>
  <div class="tracking-page">
    <div class="tracking-grid-container">
      <!-- 追踪列表 -->
      <div class="list-panel">
        <div class="list-header">
          <h1 class="title">$ ./tracked-items.list</h1>
        </div>
        <div v-if="isLoading" class="loading-state">
          <div class="loading-spinner"></div>
        </div>
        <div v-if="error" class="error-state">
          <p>{{ error }}</p>
        </div>
        <div v-if="!isLoading && trackedItems.length > 0" class="results-list">
          <div
            v-for="item in trackedItems"
            :key="item.market_hash_name"
            class="result-item"
            :class="{ selected: selectedItem?.market_hash_name === item.market_hash_name }"
            @click="selectItem(item)"
          >
            <div class="item-name">{{ item.name }}</div>
            <button class="untrack-btn" @click.stop="untrackItem(item.market_hash_name)">✕</button>
          </div>
        </div>
        <div v-if="!isLoading && trackedItems.length === 0" class="empty-state">
          <div class="empty-icon">★</div>
          <p>还没有追踪任何饰品</p>
          <router-link to="/items" class="nav-link">去市场逛逛</router-link>
        </div>
      </div>

      <!-- Other panels (price, kline, data) remain the same -->
      <div class="price-panel">
        <div v-if="selectedItem && priceData" class="price-details">
          <div class="details-header">
            <h2>{{ selectedItem.name }}</h2>
            <span class="update-time">更新时间: {{ formatTime(priceData.updateTime) }}</span>
          </div>
          <div class="price-grid">
            <template v-for="(platform, index) in Array(10).fill(null).map((_, i) => priceData.data[i] || { platform: '-', sellPrice: '-', sellCount: '-', biddingPrice: '-', biddingCount: '-' })" :key="index">
              <div class="price-card" :class="{ 'empty-card': platform.platform === '-' }">
                <div class="platform-name">{{ platform.platform }}</div>
                <div class="price-info">
                  <div class="price-line">
                    <span class="label">卖出价:</span>
                    <span class="value price" :class="{ 'highest-sell': platform.sellPrice === highestSellPrice && highestSellPrice !== null }">
                      ¥{{ platform.sellPrice }}
                    </span>
                    <span class="count">({{ platform.sellCount }})</span>
                  </div>
                  <div class="price-line">
                    <span class="label">求购价:</span>
                    <span class="value price" :class="{ 'lowest-bidding': platform.biddingPrice === lowestBiddingPrice && lowestBiddingPrice !== null }">
                      ¥{{ platform.biddingPrice }}
                    </span>
                    <span class="count">({{ platform.biddingCount }})</span>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>
        <div v-if="loadingPrice" class="loading-state">
          <div class="loading-spinner"></div>
          <span>正在获取价格...</span>
        </div>
        <div v-else-if="!selectedItem" class="placeholder-state">
          <div class="placeholder-icon">👉</div>
          <div class="placeholder-text">从左侧选择追踪的饰品</div>
        </div>
      </div>

       <div class="kline-panel">
        <div v-if="klineData.length > 0" ref="klineChart" class="kline-chart-container"></div>
        <div v-if="loadingKlineData" class="loading-state">
          <div class="loading-spinner"></div>
          <span>正在获取K线...</span>
        </div>
        <div v-else-if="klineError" class="error-state">
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

      <div class="data-panel">
        <div v-if="klineData.length > 0" ref="dataChart" class="data-chart-container"></div>
         <div v-if="loadingKlineData" class="loading-state">
          <div class="loading-spinner"></div>
          <span>正在加载数据...</span>
        </div>
         <div v-else-if="!loadingKlineData && !klineData.length && selectedItem" class="empty-state">
          <div class="empty-icon">📉</div>
          <div class="empty-text">暂无数据</div>
        </div>
        <div v-else-if="!selectedItem" class="placeholder-state">
          <div class="placeholder-icon">📈</div>
          <div class="placeholder-text">选择饰品查看数据图表</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, shallowRef, watch, nextTick } from 'vue';
import api, { client } from '../services/api';
import { useToast } from '../composables/useToast';
import * as echarts from 'echarts/core';
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent, DataZoomComponent } from 'echarts/components';
import { LineChart, BarChart } from 'echarts/charts';
import { CanvasRenderer } from 'echarts/renderers';

echarts.use([TitleComponent, TooltipComponent, LegendComponent, GridComponent, DataZoomComponent, LineChart, BarChart, CanvasRenderer]);

// Reactive State
const trackedItems = ref([]);
const isLoading = ref(false);
const error = ref(null);
const user = ref(JSON.parse(localStorage.getItem('user')));
const toast = useToast();
const selectedItem = ref(null);
const priceData = ref(null);
const loadingPrice = ref(false);
const klineData = ref([]);
const loadingKlineData = ref(false);
const klineError = ref(null);
const highestSellPrice = ref(null);
const lowestBiddingPrice = ref(null);
const klineChart = ref(null);
const myKlineChart = shallowRef(null);
const dataChart = ref(null);
const myDataChart = shallowRef(null);

// Methods
async function fetchTrackedItems() {
  if (!user.value) return;
  isLoading.value = true;
  error.value = null;
  try {
    const response = await client.get(`/track/list/${user.value.email}`);
    trackedItems.value = response.data;
  } catch (err) {
    error.value = '无法加载追踪列表。';
    toast.error(error.value);
  } finally {
    isLoading.value = false;
  }
}

async function untrackItem(marketHashName) {
  if (!user.value) return;
  try {
    await client.post('/track/remove', { email: user.value.email, market_hash_name: marketHashName });
    toast.success('已取消追踪！');
    fetchTrackedItems();
    if (selectedItem.value?.market_hash_name === marketHashName) {
      selectedItem.value = null;
    }
  } catch (err) {
    toast.error('取消追踪失败。');
  }
}

const selectItem = async (item) => {
  selectedItem.value = item;
  loadingPrice.value = true;
  loadingKlineData.value = true;
  klineData.value = [];
  klineError.value = null;
  highestSellPrice.value = null;
  lowestBiddingPrice.value = null;

  try {
    const priceResult = await api.getItemPrice(item.market_hash_name);
    if (priceResult.success) {
      priceData.value = { data: priceResult.data, updateTime: priceResult.data[0]?.updateTime || Date.now() / 1000 };
      
      let maxSell = 0;
      let minBidding = Infinity;
      priceResult.data.forEach(p => {
        if (p.platform === 'Steam' || p.sellPrice === 0 || p.biddingPrice === 0) return;
        if (p.sellPrice > maxSell) maxSell = p.sellPrice;
        if (p.biddingPrice < minBidding) minBidding = p.biddingPrice;
      });
      highestSellPrice.value = maxSell > 0 ? maxSell : null;
      lowestBiddingPrice.value = minBidding !== Infinity ? minBidding : null;
    } else {
      priceData.value = null;
    }
  } catch (e) { console.error(e); } finally { loadingPrice.value = false; }

  try {
    const klineResult = await api.getItemKlineData(item.market_hash_name);
    if (klineResult.success && klineResult.data.length > 0) {
      klineData.value = klineResult.data;
    } else {
      klineError.value = klineResult.success ? '暂无K线数据' : (klineResult.error?.message || '获取K线数据失败');
    }
  } catch (e) { console.error(e); klineError.value = '获取K线数据失败'; } finally { loadingKlineData.value = false; }
};

const formatTime = (timestamp) => timestamp ? new Date(timestamp * 1000).toLocaleString('zh-CN') : '';

// ECharts
const upColor = '#00ff00', downColor = '#ff0000';
function splitData(rawData) {
  let categoryData = [], candlestickData = [], totalCountData = [], buyCountData = [], sellCountData = [], turnoverData = [], volumeData = [];
  rawData.forEach(item => {
    categoryData.push(new Date(item.timestamp * 1000).toLocaleDateString('zh-CN'));
    candlestickData.push([parseFloat(item.buy_price), parseFloat(item.price), Math.min(item.price, item.buy_price), Math.max(item.price, item.buy_price)]);
    totalCountData.push(parseInt(item.total_count));
    buyCountData.push(parseInt(item.buy_count));
    sellCountData.push(parseInt(item.sell_count));
    turnoverData.push(parseFloat(item.turnover));
    volumeData.push(parseInt(item.volume));
  });
  return { categoryData, candlestickData, totalCountData, buyCountData, sellCountData, turnoverData, volumeData };
}

function initAndupdateCharts() {
  if (myKlineChart.value) { myKlineChart.value.dispose(); }
  if (myDataChart.value) { myDataChart.value.dispose(); }
  if (!klineChart.value || !dataChart.value) return;

  myKlineChart.value = echarts.init(klineChart.value, 'dark');
  myDataChart.value = echarts.init(dataChart.value, 'dark');
  
  const { categoryData, candlestickData, totalCountData, buyCountData, sellCountData, turnoverData, volumeData } = splitData(klineData.value);

  myKlineChart.value.setOption({
    title: { text: 'K-Line Chart', left: 'center', textStyle: { color: '#00ff00', fontSize: 16 } },
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    legend: { data: ['在售最低价', '求购最高价', '交易个数'], top: '8%', textStyle: { color: '#ccc' } },
    grid: { left: '10%', right: '10%', bottom: '15%', top: '18%' },
    xAxis: { type: 'category', data: categoryData, scale: true },
    yAxis: [{ type: 'value', scale: true }, { type: 'value', scale: true, position: 'right' }],
    dataZoom: [{ type: 'inside', start: 70, end: 100 }, { type: 'slider', top: '90%' }],
    series: [
      { name: '在售最低价', type: 'line', data: candlestickData.map(i => i[1]), smooth: true, showSymbol: false, lineStyle: { color: upColor } },
      { name: '求购最高价', type: 'line', data: candlestickData.map(i => i[0]), smooth: true, showSymbol: false, lineStyle: { color: downColor } },
      { name: '交易个数', type: 'bar', data: volumeData, yAxisIndex: 1, itemStyle: { color: '#ADFF2F', opacity: 0.5 } }
    ]
  });

  myDataChart.value.setOption({
    title: { text: '成交量分析', left: 'center', textStyle: { color: '#00ff00', fontSize: 16 } },
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    legend: { data: ['存世量', '求购数量', '在售数量', '交易额'], top: '8%', textStyle: { color: '#ccc' } },
    grid: { left: '10%', right: '10%', bottom: '15%', top: '18%' },
    xAxis: { type: 'category', data: categoryData },
    yAxis: [{type: 'value'}, {type: 'value', position: 'right'}, {type: 'value', position: 'right', offset: 80}],
    dataZoom: [{ type: 'inside', start: 70, end: 100 }, { type: 'slider', top: '90%' }],
    series: [
      { name: '存世量', type: 'line', data: totalCountData, yAxisIndex: 0, smooth: true, showSymbol: false },
      { name: '求购数量', type: 'line', data: buyCountData, yAxisIndex: 1, smooth: true, showSymbol: false },
      { name: '在售数量', type: 'line', data: sellCountData, yAxisIndex: 1, smooth: true, showSymbol: false },
      { name: '交易额', type: 'bar', data: turnoverData, yAxisIndex: 2 }
    ]
  });
}

watch(klineData, (newVal) => {
  if (newVal && newVal.length > 0) {
    nextTick(initAndupdateCharts);
  } else {
    if (myKlineChart.value) { myKlineChart.value.dispose(); myKlineChart.value = null; }
    if (myDataChart.value) { myDataChart.value.dispose(); myDataChart.value = null; }
  }
});

onMounted(fetchTrackedItems);
</script>

<style scoped>
.tracking-page { width: 100%; max-width: 1400px; padding: 24px; margin: 40px auto 0; animation: fadeIn 0.4s ease; }
.tracking-grid-container { display: grid; grid-template-columns: 0.8fr 2.2fr; grid-template-rows: auto auto 1fr; gap: 20px; grid-template-areas: "list price" "list kline" "list data"; }
.list-panel, .price-panel, .kline-panel, .data-panel { background: rgba(0, 0, 0, 0.4); border: 1px solid #00ff41; border-radius: 8px; padding: 16px; display: flex; flex-direction: column; }
.list-panel { grid-area: list; }
.price-panel { grid-area: price; min-height: 200px; }
.kline-panel { grid-area: kline; min-height: 300px; }
.data-panel { grid-area: data; min-height: 300px; }
.list-header .title { font-family: 'Courier New', monospace; font-size: 20px; color: #00ff41; margin: 0 0 16px 0; }
.results-list { flex-grow: 1; overflow-y: auto; }
.result-item { padding: 16px; border-bottom: 1px solid rgba(0, 255, 65, 0.2); cursor: pointer; transition: all 0.2s ease; display: flex; justify-content: space-between; align-items: center; }
.result-item:hover { background: rgba(0, 255, 65, 0.1); }
.result-item.selected { background: rgba(0, 255, 65, 0.2); }
.item-name { color: #00ff41; font-family: 'Courier New', monospace; }
.untrack-btn { background: transparent; border: none; color: rgba(255, 107, 107, 0.7); font-size: 20px; cursor: pointer; }
.untrack-btn:hover { color: #ff6b6b; }
.loading-state, .error-state, .empty-state, .placeholder-state { display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%; min-height: 150px; color: rgba(0, 255, 65, 0.7); font-family: 'Courier New', monospace; }
.loading-spinner { border: 4px solid rgba(0, 255, 65, 0.2); border-left-color: #00ff41; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin-bottom: 10px; }
@keyframes spin { to { transform: rotate(360deg); } }
.empty-icon, .placeholder-icon { font-size: 48px; margin-bottom: 20px; color: #00ff41; }
.details-header { margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid rgba(0, 255, 65, 0.3); display: flex; justify-content: space-between; }
.details-header h2 { color: #00ff41; font-size: 18px; }
.update-time { font-size: 12px; color: rgba(0, 255, 65, 0.6); }
.price-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; }
.price-card { background: rgba(0, 255, 65, 0.05); border: 1px solid rgba(0, 255, 65, 0.2); border-radius: 4px; padding: 8px; }
.platform-name { font-weight: bold; color: #fff; font-size: 13px; }
.price-line { display: flex; justify-content: space-between; margin-top: 6px; font-size: 12px; }
.label { color: rgba(255, 255, 255, 0.7); }
.value.price { color: #00ff41; }
.count { color: rgba(255, 255, 255, 0.5); }
.value.price.highest-sell,
.value.price.lowest-bidding {
  font-weight: bold;
  text-shadow: 0 0 8px;
}
.value.price.highest-sell { color: #fce38a; }
.value.price.lowest-bidding { color: #95e1d3; }
.kline-chart-container, .data-chart-container { width: 100%; height: 100%; min-height: 280px; }
.nav-link { margin-top: 20px; color: #00ff41; text-decoration: none; border: 1px solid #00ff41; padding: 10px 20px; border-radius: 4px; transition: all 0.2s; }
.nav-link:hover { background: rgba(0, 255, 65, 0.1); }
</style>