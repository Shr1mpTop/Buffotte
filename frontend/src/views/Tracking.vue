<template>
  <div ref="rootEl" class="tracking-page">
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
        TRACKING MONITOR &nbsp;·&nbsp; {{ trackedItems.length }} ITEMS TRACKED
      </div>
    </header>

    <!-- MAIN LAYOUT -->
    <div class="main-grid">
      <!-- LEFT: Tracked Items Panel -->
      <div ref="listPanelEl" class="panel-card list-panel">
        <div class="pc-hd">
          <span class="pc-dot"></span>追踪列表
          <span v-if="trackedItems.length" class="result-count">{{
            trackedItems.length
          }}</span>
        </div>

        <!-- Loading -->
        <div v-if="isLoading" class="panel-empty">
          <div class="ld-spinner"></div>
          <span class="empty-line">正在加载...</span>
        </div>

        <!-- Error -->
        <div v-if="error" class="panel-empty">
          <div class="empty-line error">{{ error }}</div>
        </div>

        <!-- Tracked Items List -->
        <div v-if="!isLoading && trackedItems.length > 0" class="results-list">
          <div
            v-for="(item, idx) in trackedItems"
            :key="item.market_hash_name"
            class="result-item"
            :class="{
              selected:
                selectedItem?.market_hash_name === item.market_hash_name,
            }"
            @click="selectItem(item)"
            :ref="(el) => { if (el) itemRefs[idx] = el }"
          >
            <div class="ri-info">
              <div class="ri-name">{{ item.name }}</div>
              <div class="ri-profit-badge" v-if="getItemProfitBadge(item)">
                <span :class="getItemProfitBadge(item).cls">
                  {{ getItemProfitBadge(item).text }}
                </span>
              </div>
            </div>
            <button
              class="untrack-btn"
              @click.stop="untrackItem(item.market_hash_name)"
            >
              ✕
            </button>
          </div>
        </div>

        <!-- Empty State -->
        <div
          v-if="!isLoading && trackedItems.length === 0"
          class="panel-empty col"
        >
          <div class="empty-line">> 还没有追踪任何饰品</div>
          <router-link to="/items" class="nav-link">
            → 去饰品市场逛逛
          </router-link>
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
            class="untrack-btn-lg"
            @click="untrackItem(selectedItem.market_hash_name)"
          >
            ✕ 取消追踪
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
                    highlight:
                      platform.sellPrice === highestSellPrice &&
                      highestSellPrice !== null,
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
                    'highlight-yellow':
                      platform.biddingPrice === lowestBiddingPrice &&
                      lowestBiddingPrice !== null,
                  }"
                  >¥{{ platform.biddingPrice }}</span
                >
                <span class="pf-cnt">({{ platform.biddingCount }})</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Loading Price -->
        <div v-if="loadingPrice" class="panel-card panel-loading">
          <div class="ld-spinner"></div>
          <span>正在获取价格数据...</span>
        </div>

        <!-- Placeholder when no item selected -->
        <div
          v-if="!selectedItem && !isLoading"
          class="panel-card"
        >
          <div class="pc-hd">
            <span class="pc-dot"></span>饰品详情
          </div>
          <div class="panel-empty">
            <div class="empty-line">> 从左侧选择追踪的饰品</div>
          </div>
        </div>

        <!-- Profit Prediction Panel -->
        <div ref="profitPanelEl" class="panel-card profit-panel" v-if="selectedItem && (profitLoading || profitData)">
          <div class="pc-hd">
            <span class="pc-dot"></span>7天预测利润
            <div v-if="profitLoading" class="refresh-badge">
              <span class="refresh-dot"></span>预测中
            </div>
          </div>
          <div v-if="profitLoading" class="panel-loading-inline">
            <div class="ld-spinner sm"></div>
            <span>LGBM 模型预测中...</span>
          </div>
          <div v-else-if="profitError" class="panel-empty">
            <div class="empty-line error">{{ profitError }}</div>
          </div>
          <div v-else-if="profitData" class="profit-content">
            <div class="profit-summary">
              <div class="ps-item">
                <div class="ps-label">当前价格</div>
                <div class="ps-value">¥{{ profitData.current_price ?? '-' }}</div>
              </div>
              <div class="ps-item">
                <div class="ps-label">7天预测价</div>
                <div class="ps-value predicted">¥{{ profitData.predicted_price_7d }}</div>
                <div class="ps-range" v-if="profitData.predicted_lower && profitData.predicted_upper">
                  ¥{{ profitData.predicted_lower }} ~ ¥{{ profitData.predicted_upper }}
                  <span :class="'confidence-' + profitData.confidence">{{ profitData.confidence }}</span>
                </div>
              </div>
            </div>
            <div class="profit-table" v-if="profitData.profit_by_platform && Object.keys(profitData.profit_by_platform).length">
              <div class="pt-header">
                <span class="pt-col-name">平台</span>
                <span class="pt-col">卖出价</span>
                <span class="pt-col">手续费</span>
                <span class="pt-col">提现费</span>
                <span class="pt-col">净利润</span>
                <span class="pt-col">利润率</span>
                <span class="pt-col">年化</span>
              </div>
              <div
                v-for="(pdata, pkey) in profitData.profit_by_platform"
                :key="pkey"
                class="pt-row"
                :class="{ 'best-profit': isBestProfit(pkey) }"
              >
                <span class="pt-col-name">{{ pdata.display_name || pkey }}</span>
                <span class="pt-col">¥{{ pdata.sell_price }}</span>
                <span class="pt-col fee">¥{{ pdata.sell_fee }}</span>
                <span class="pt-col fee">¥{{ pdata.withdraw_fee }}</span>
                <span class="pt-col" :class="pdata.net_profit >= 0 ? 'profit-positive' : 'profit-negative'">
                  ¥{{ pdata.net_profit }}
                </span>
                <span class="pt-col" :class="pdata.profit_rate >= 0 ? 'profit-positive' : 'profit-negative'">
                  {{ pdata.profit_rate }}%
                </span>
                <span class="pt-col" :class="pdata.annualized_return >= 0 ? 'profit-positive' : 'profit-negative'">
                  {{ pdata.annualized_return }}%
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- K-line Chart -->
        <div ref="klinePanelEl" class="panel-card chart-panel">
          <div class="pc-hd">
            <span class="pc-dot"></span>K线走势
            <div v-if="isRefreshingKline" class="refresh-badge">
              <span class="refresh-dot"></span>刷新中
            </div>
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
import api, { client } from '../services/api';
import { useToast } from '../composables/useToast';
import * as echarts from 'echarts/core';
import {
  TitleComponent, TooltipComponent, LegendComponent, GridComponent,
  DataZoomComponent, MarkPointComponent, MarkLineComponent,
} from 'echarts/components';
import { LineChart, BarChart } from 'echarts/charts';
import { CanvasRenderer } from 'echarts/renderers';
import gsap from 'gsap';
import { CSSPlugin } from 'gsap/CSSPlugin';

gsap.registerPlugin(CSSPlugin);

echarts.use([
  TitleComponent, TooltipComponent, LegendComponent, GridComponent,
  DataZoomComponent, MarkPointComponent, MarkLineComponent,
  LineChart, BarChart, CanvasRenderer,
]);

const toast = useToast();

// DOM refs
const rootEl = ref(null);
const matrixCanvas = ref(null);
const headerEl = ref(null);
const typedEl = ref(null);
const listPanelEl = ref(null);
const infoBarEl = ref(null);
const priceStripEl = ref(null);
const klinePanelEl = ref(null);
const dataPanelEl = ref(null);
const klineChart = ref(null);
const dataChart = ref(null);
const itemRefs = reactive({});

// Chart instances
const myKlineChart = shallowRef(null);
const myDataChart = shallowRef(null);

// State
const trackedItems = ref([]);
const isLoading = ref(false);
const error = ref(null);
const user = ref(JSON.parse(localStorage.getItem('user')));
const selectedItem = ref(null);
const priceData = ref(null);
const loadingPrice = ref(false);
const klineData = ref([]);
const loadingKlineData = ref(false);
const klineError = ref(null);
const highestSellPrice = ref(null);
const lowestBiddingPrice = ref(null);
const isRefreshingKline = ref(false);
const profitData = ref(null);
const profitLoading = ref(false);
const profitError = ref(null);
const profitPanelEl = ref(null);
const trackedProfitMap = ref({}); // {market_hash_name: {best_rate, best_platform}}

// Matrix rain
let _raf = null;
let _matrixCleanup = null;
let _ctx = null;

// Colors
const upColor = '#00ff00';
const downColor = '#ff0000';

// Computed: display platforms
const displayPlatforms = computed(() => {
  if (!priceData.value) return [];
  return Array(10).fill(null).map((_, i) =>
    priceData.value.data[i] || {
      platform: '-', sellPrice: '-', sellCount: '-',
      biddingPrice: '-', biddingCount: '-',
    }
  );
});

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

    tl.fromTo(listPanelEl.value,
      { opacity: 0, x: -36 },
      { opacity: 1, x: 0, duration: 0.5, ease: 'power2.out' },
      '-=0.2'
    );

    tl.fromTo([klinePanelEl.value, dataPanelEl.value],
      { opacity: 0, y: 30 },
      { opacity: 1, y: 0, duration: 0.55, stagger: 0.12, ease: 'power3.out' },
      '-=0.15'
    );

    // Glow pulse on panel dots
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

// Animate list items entrance
const animateListItems = () => {
  const items = Object.values(itemRefs);
  if (items.length) {
    gsap.fromTo(items,
      { opacity: 0, x: -12 },
      { opacity: 1, x: 0, duration: 0.3, stagger: 0.04, ease: 'power2.out' }
    );
  }
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

// --- Fetch tracked items ---
async function fetchTrackedItems() {
  if (!user.value) return;
  isLoading.value = true;
  error.value = null;
  try {
    const response = await client.get(`/track/list/${user.value.email}`);
    trackedItems.value = response.data;
    await nextTick();
    animateListItems();
  } catch (err) {
    error.value = '无法加载追踪列表。';
    toast.error(error.value);
  } finally {
    isLoading.value = false;
  }
}

// --- Untrack item ---
async function untrackItem(marketHashName) {
  if (!user.value) return;
  try {
    await client.post('/track/remove', {
      email: user.value.email,
      market_hash_name: marketHashName,
    });
    toast.success('已取消追踪！');
    fetchTrackedItems();
    if (selectedItem.value?.market_hash_name === marketHashName) {
      selectedItem.value = null;
    }
  } catch (err) {
    toast.error('取消追踪失败。');
  }
}

// --- Select item ---
const selectItem = async (item) => {
  selectedItem.value = item;
  loadingPrice.value = true;
  loadingKlineData.value = true;
  klineData.value = [];
  klineError.value = null;
  isRefreshingKline.value = false;
  highestSellPrice.value = null;
  lowestBiddingPrice.value = null;
  profitData.value = null;
  profitError.value = null;
  profitLoading.value = true;

  // Fetch price
  try {
    const priceResult = await api.getItemPrice(item.market_hash_name);
    if (priceResult.success) {
      priceData.value = {
        data: priceResult.data,
        updateTime: priceResult.data[0]?.updateTime || Date.now() / 1000,
      };
      let maxSell = 0;
      let minBidding = Infinity;
      priceResult.data.forEach((p) => {
        if (p.platform === 'Steam' || p.sellPrice === 0 || p.biddingPrice === 0) return;
        if (p.sellPrice > maxSell) maxSell = p.sellPrice;
        if (p.biddingPrice < minBidding) minBidding = p.biddingPrice;
      });
      highestSellPrice.value = maxSell > 0 ? maxSell : null;
      lowestBiddingPrice.value = minBidding !== Infinity ? minBidding : null;
      await nextTick();
      animateInfoBar();
      animatePriceCards();
    } else {
      priceData.value = null;
    }
  } catch (e) {
    console.error(e);
  } finally {
    loadingPrice.value = false;
  }

  // Phase 1: 快速加载缓存K线数据
  try {
    const cachedResult = await api.getCachedItemKlineData(item.market_hash_name);
    if (cachedResult.success && cachedResult.data.length > 0) {
      klineData.value = cachedResult.data;
      loadingKlineData.value = false;

      // Phase 2: 后台异步刷新最新数据
      isRefreshingKline.value = true;
      api.refreshItemKlineData(item.market_hash_name).then((freshResult) => {
        if (selectedItem.value?.market_hash_name !== item.market_hash_name) return;
        if (freshResult.success && freshResult.data.length > 0) {
          klineData.value = freshResult.data;
        }
      }).catch((e) => {
        console.error('后台K线刷新失败:', e);
      }).finally(() => {
        if (selectedItem.value?.market_hash_name === item.market_hash_name) {
          isRefreshingKline.value = false;
        }
      });
    } else {
      // 无缓存数据 — 直接从 bufftracker API 获取（与 Items.vue 相同）
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
      } catch (e) {
        console.error(e);
        klineError.value = '获取K线数据失败';
      } finally {
        loadingKlineData.value = false;
      }
    }
  } catch (e) {
    // 缓存读取失败 — 降级走 bufftracker API
    console.error(e);
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
    } catch (e2) {
      console.error(e2);
      klineError.value = '获取K线数据失败';
    } finally {
      loadingKlineData.value = false;
    }
  }

  // Phase 3: 预测利润
  api.predictItemProfit(item.market_hash_name).then((result) => {
    if (selectedItem.value?.market_hash_name !== item.market_hash_name) return;
    if (result.success && result.data) {
      profitData.value = result.data;
      // 更新追踪列表的利润标记
      updateTrackedProfitMap(result.data);
    } else {
      profitError.value = result.error || '数据不足，无法预测';
    }
  }).catch((e) => {
    console.error('利润预测失败:', e);
    profitError.value = '预测失败';
  }).finally(() => {
    if (selectedItem.value?.market_hash_name === item.market_hash_name) {
      profitLoading.value = false;
    }
  });
};

// --- Profit helpers ---
const updateTrackedProfitMap = (data) => {
  if (!data.profit_by_platform) return;
  let bestRate = -Infinity;
  let bestPlatform = null;
  for (const [pkey, pdata] of Object.entries(data.profit_by_platform)) {
    if (pdata.profit_rate > bestRate) {
      bestRate = pdata.profit_rate;
      bestPlatform = pkey;
    }
  }
  trackedProfitMap.value[data.market_hash_name] = {
    best_rate: bestRate,
    best_platform: bestPlatform,
  };
};

const getItemProfitBadge = (item) => {
  const info = trackedProfitMap.value[item.market_hash_name];
  if (!info) return null;
  const rate = info.best_rate;
  if (rate > 0) {
    return { text: `+${rate.toFixed(1)}%`, cls: 'badge-profit' };
  } else if (rate < 0) {
    return { text: `${rate.toFixed(1)}%`, cls: 'badge-loss' };
  }
  return null;
};

const isBestProfit = (pkey) => {
  if (!profitData.value?.profit_by_platform) return false;
  let bestRate = -Infinity;
  let bestKey = null;
  for (const [k, v] of Object.entries(profitData.value.profit_by_platform)) {
    if (v.profit_rate > bestRate) {
      bestRate = v.profit_rate;
      bestKey = k;
    }
  }
  return pkey === bestKey;
};
const formatTime = (timestamp) => {
  if (!timestamp) return '';
  return new Date(timestamp * 1000).toLocaleString('zh-CN');
};

// --- ECharts data processing ---
function splitData(rawData) {
  let categoryData = [], candlestickData = [], totalCountData = [];
  let buyCountData = [], sellCountData = [], turnoverData = [], volumeData = [];
  if (!rawData?.length) return { categoryData, candlestickData, totalCountData, buyCountData, sellCountData, turnoverData, volumeData };

  rawData.forEach((item) => {
    if (!item || item.timestamp === undefined) return;
    const price = parseFloat(item.price);
    const buyPrice = parseFloat(item.buy_price);
    categoryData.push(new Date(item.timestamp * 1000).toLocaleDateString('zh-CN'));
    candlestickData.push([buyPrice, price, Math.min(price, buyPrice), Math.max(price, buyPrice)]);
    totalCountData.push(parseInt(item.total_count));
    buyCountData.push(parseInt(item.buy_count));
    sellCountData.push(parseInt(item.sell_count));
    turnoverData.push(parseFloat(item.turnover));
    volumeData.push(parseInt(item.volume));
  });
  return { categoryData, candlestickData, totalCountData, buyCountData, sellCountData, turnoverData, volumeData };
}

// --- K-line chart config ---
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
        if (p.seriesName === '在售最低价' && p.data !== undefined)
          res += `在售最低价: ${p.data.toFixed(2)}<br/>`;
        else if (p.seriesName === '求购最高价' && p.data !== undefined)
          res += `求购最高价: ${p.data.toFixed(2)}<br/>`;
        else if (p.seriesName === '交易个数' && p.data !== undefined)
          res += `交易个数: ${p.data}<br/>`;
      });
      return res;
    },
  },
  legend: {
    data: ['在售最低价', '求购最高价', '交易个数'],
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

// --- Init data chart ---
const initDataChart = async () => {
  if (!klineData.value?.length) return;
  await nextTick();
  if (!dataChart.value) return;
  if (myDataChart.value) myDataChart.value.dispose();
  myDataChart.value = echarts.init(dataChart.value, 'dark');
  updateDataChart();
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
        name: '在售最低价', type: 'line',
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
        name: '求购最高价', type: 'line',
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
onMounted(() => {
  initMatrix();
  initGSAP();

  setTimeout(async () => {
    if (!typedEl.value) return;
    await typewriter(typedEl.value, './tracking-monitor.sh --watch=live', 42);
  }, 300);

  fetchTrackedItems();
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
.tracking-page {
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
  .main-grid { grid-template-columns: 1fr; }
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

/* === List Panel === */
.list-panel {
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 120px);
  position: sticky;
  top: 20px;
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
  transition: background 0.2s;
  display: flex;
  justify-content: space-between;
  align-items: center;
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
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
  min-width: 0;
}

/* Untrack button (small, in list) */
.untrack-btn {
  background: transparent;
  border: none;
  color: rgba(255, 80, 80, 0.5);
  font-size: 14px;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 3px;
  transition: color 0.2s, background 0.2s;
  flex-shrink: 0;
}
.untrack-btn:hover {
  color: #ff4444;
  background: rgba(255, 80, 80, 0.1);
}

/* Untrack button (large, in info bar) */
.untrack-btn-lg {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 16px;
  background: rgba(255, 80, 80, 0.06);
  border: 1px solid rgba(255, 80, 80, 0.25);
  border-radius: 5px;
  color: rgba(255, 80, 80, 0.8);
  font-family: 'Share Tech Mono', monospace;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.25s ease;
}
.untrack-btn-lg:hover {
  background: rgba(255, 80, 80, 0.12);
  border-color: rgba(255, 80, 80, 0.4);
  color: #ff4444;
  transform: translateY(-1px);
}

/* Nav link */
.nav-link {
  margin-top: 12px;
  color: var(--primary-green);
  text-decoration: none;
  font-size: 13px;
  padding: 6px 14px;
  border: 1px solid rgba(0, 255, 65, 0.3);
  border-radius: 5px;
  transition: all 0.25s;
}
.nav-link:hover {
  background: rgba(0, 255, 65, 0.08);
  border-color: rgba(0, 255, 65, 0.5);
}

/* Refresh badge */
.refresh-badge {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 10px;
  color: rgba(0, 255, 65, 0.5);
}
.refresh-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--primary-green);
  animation: spin-pulse 1s ease-in-out infinite;
}
@keyframes spin-pulse {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1.2); }
}

/* Empty state */
.panel-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 16px;
  flex-grow: 1;
}
.panel-empty.col {
  flex-direction: column;
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
.pf-val.highlight {
  color: #ff4444 !important;
  text-shadow: 0 0 8px rgba(255, 68, 68, 0.6);
}
.pf-val.highlight-yellow {
  color: #ffdd00 !important;
  text-shadow: 0 0 8px rgba(255, 221, 0, 0.6);
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
  .list-panel {
    position: static;
    max-height: 360px;
  }
  .info-bar {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}

/* === Profit Prediction Panel === */
.profit-panel {
  display: flex;
  flex-direction: column;
}

.profit-content {
  padding: 12px 14px;
}

.profit-summary {
  display: flex;
  gap: 24px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.ps-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ps-label {
  font-size: 10px;
  color: rgba(0, 255, 65, 0.4);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.ps-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--primary-green);
}

.ps-value.predicted {
  color: #00e5ff;
  text-shadow: 0 0 8px rgba(0, 229, 255, 0.3);
}

.ps-range {
  font-size: 10px;
  color: rgba(0, 255, 65, 0.35);
}

.confidence-high { color: #00ff41; margin-left: 4px; }
.confidence-medium { color: #ffdd00; margin-left: 4px; }
.confidence-low { color: #ff6b6b; margin-left: 4px; }

/* Profit table */
.profit-table {
  width: 100%;
  overflow-x: auto;
}

.pt-header, .pt-row {
  display: grid;
  grid-template-columns: 90px repeat(6, 1fr);
  gap: 4px;
  padding: 6px 0;
  font-size: 12px;
  align-items: center;
}

.pt-header {
  color: rgba(0, 255, 65, 0.4);
  border-bottom: 1px solid rgba(0, 255, 65, 0.08);
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.pt-row {
  border-bottom: 1px solid rgba(0, 255, 65, 0.04);
  transition: background 0.2s;
}

.pt-row:hover {
  background: rgba(0, 255, 65, 0.03);
}

.pt-row.best-profit {
  background: rgba(0, 255, 65, 0.06);
  border-left: 2px solid var(--primary-green);
}

.pt-col-name {
  color: rgba(0, 255, 65, 0.6);
  font-weight: 600;
}

.pt-col {
  color: rgba(0, 255, 65, 0.5);
  text-align: right;
}

.pt-col.fee {
  color: rgba(255, 165, 0, 0.5);
}

.profit-positive {
  color: #00ff41 !important;
  font-weight: 700;
}

.profit-negative {
  color: #ff4444 !important;
  font-weight: 700;
}

/* List item profit badge */
.ri-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ri-profit-badge {
  font-size: 10px;
}

.badge-profit {
  color: #00ff41;
  font-weight: 600;
}

.badge-loss {
  color: #ff4444;
  font-weight: 600;
}
</style>
