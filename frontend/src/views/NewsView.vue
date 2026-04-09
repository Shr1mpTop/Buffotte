<template>
  <div class="news-view" ref="newsViewContainer">
    <!-- ─── 数据看板 ─────────────────────────────────────── -->
    <div class="dashboard">
      <div class="dash-card">
        <span class="dash-label">📊 新闻总量</span>
        <span class="dash-value">{{ stats.total || 0 }}</span>
      </div>
      <div class="dash-card">
        <span class="dash-label">📡 信息来源</span>
        <span class="dash-value">{{ stats.source_top?.length || 0 }}</span>
      </div>
      <div class="dash-card">
        <span class="dash-label">📅 覆盖时段</span>
        <span class="dash-value small">{{ timeRangeLabel }}</span>
      </div>
      <div class="dash-card">
        <span class="dash-label">⏱ 最新资讯</span>
        <span class="dash-value small">{{ latestNewsTime }}</span>
      </div>
      <!-- mini 趋势条 -->
      <div class="dash-card wide">
        <span class="dash-label">7日趋势</span>
        <div class="mini-chart">
          <div
            v-for="(d, i) in stats.daily_trend || []"
            :key="i"
            class="mini-bar"
            :style="{ height: miniBarHeight(d.count) + 'px' }"
            :title="`${d.day}: ${d.count}条`"
          ></div>
        </div>
      </div>
    </div>

    <!-- ─── 市场洞察（可折叠） ───────────────────────────── -->
    <div class="insight-panel" v-if="summary">
      <div class="insight-header" @click="insightOpen = !insightOpen">
        <h2 class="insight-title">💡 市场洞察</h2>
        <span class="insight-toggle" :class="{ open: insightOpen }">▾</span>
      </div>
      <transition name="fold">
        <div class="insight-body" v-show="insightOpen">
          <div class="insight-content" v-html="renderedSummary"></div>
        </div>
      </transition>
    </div>

    <!-- ─── 筛选工具栏 ──────────────────────────────────── -->
    <div class="filter-bar">
      <div class="filter-group">
        <button
          class="filter-chip"
          :class="{ active: !activeCategory }"
          @click="setCategory(null)"
        >
          全部
        </button>
        <button
          v-for="cat in allCategories"
          :key="cat"
          class="filter-chip"
          :class="{ active: activeCategory === cat }"
          @click="setCategory(cat)"
        >
          {{ categoryIcon(cat) }} {{ cat }}
        </button>
      </div>
      <div class="filter-group">
        <select class="time-select" v-model="activeDays" @change="onFilterChange">
          <option :value="null">全部时间</option>
          <option :value="1">最近 24h</option>
          <option :value="3">最近 3 天</option>
          <option :value="7">最近 7 天</option>
          <option :value="30">最近 30 天</option>
        </select>
      </div>
    </div>

    <!-- ─── 分类统计条 ──────────────────────────────────── -->
    <div class="category-stats" v-if="stats.category_distribution?.length">
      <div
        v-for="cat in stats.category_distribution"
        :key="cat.category"
        class="cat-bar-wrap"
        :title="`${cat.category}: ${cat.count}条`"
      >
        <span class="cat-bar-label">{{ cat.category }}</span>
        <div class="cat-bar-track">
          <div
            class="cat-bar-fill"
            :style="{ width: catBarWidth(cat.count) + '%' }"
          ></div>
        </div>
        <span class="cat-bar-count">{{ cat.count }}</span>
      </div>
    </div>

    <!-- ─── 新闻卡片网格 ────────────────────────────────── -->
    <div class="news-grid">
      <div
        class="news-card"
        :class="{ highlighted: item.highlighted }"
        v-for="item in news"
        :key="item.id"
      >
        <div class="card-top">
          <span class="cat-badge" v-if="item.category">{{
            categoryIcon(item.category)
          }} {{ item.category }}</span>
          <span class="cat-badge uncategorized" v-else>未分类</span>
        </div>
        <h3 class="news-title">
          <a :href="item.url" target="_blank">{{ item.title }}</a>
        </h3>
        <p class="news-preview">{{ item.preview }}</p>
        <div class="news-meta">
          <span class="news-source">{{ item.source }}</span>
          <span class="news-time">{{ formatTime(item.publish_time) }}</span>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-indicator">
      <div class="loading-dots"><span></span><span></span><span></span></div>
    </div>
    <div v-if="!loading && page > totalPages && news.length" class="no-more-news">
      - 数据流终止 -
    </div>
    <div v-if="!loading && !news.length && !firstLoad" class="empty-state">
      <div class="empty-icon">⬡</div>
      <p>暂无匹配的资讯数据</p>
    </div>

    <!-- 返回顶部 -->
    <button @click="scrollToTop" class="rocket-button" v-show="showRocket">▲</button>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { marked } from "marked";
import DOMPurify from "dompurify";

// ─── 状态 ─────────────────────────────────────────────────────
const newsViewContainer = ref(null);
const summary = ref(null);
const summaryId = ref(null);
const renderedSummary = ref("");
const insightOpen = ref(false);

const news = ref([]);
const loading = ref(false);
const firstLoad = ref(true);
const page = ref(1);
const totalPages = ref(1);
const showRocket = ref(false);

const stats = ref({});
const activeCategory = ref(null);
const activeDays = ref(null);

// ─── 计算属性 ─────────────────────────────────────────────────
const allCategories = computed(() => stats.value.categories || []);

const timeRangeLabel = computed(() => {
  const tr = stats.value.time_range;
  if (!tr?.earliest || !tr?.latest) return "—";
  const fmt = (s) => s.slice(0, 10);
  return `${fmt(tr.earliest)} ~ ${fmt(tr.latest)}`;
});

const latestNewsTime = computed(() => {
  const tr = stats.value.time_range;
  if (!tr?.latest) return "—";
  return new Date(tr.latest).toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
});

// ─── 工具函数 ─────────────────────────────────────────────────
const categoryIcon = (cat) => {
  const map = {
    赛事动态: "🏆",
    版本更新: "🔧",
    市场行情: "📈",
    饰品资讯: "💎",
    社区热点: "🔥",
    其他: "📌",
  };
  return map[cat] || "📌";
};

const formatTime = (timeStr) => {
  if (!timeStr) return "—";
  return new Date(timeStr).toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
};

const miniBarHeight = (count) => {
  const max = Math.max(...(stats.value.daily_trend || []).map((d) => d.count), 1);
  return Math.max(4, (count / max) * 36);
};

const catBarWidth = (count) => {
  const max = Math.max(...(stats.value.category_distribution || []).map((c) => c.count), 1);
  return (count / max) * 100;
};

// ─── 数据获取 ─────────────────────────────────────────────────
const fetchStats = async () => {
  try {
    const res = await fetch("/api/news/stats");
    if (res.ok) stats.value = await res.json();
  } catch (e) {
    console.error("Stats fetch error:", e);
  }
};

const fetchSummary = async () => {
  try {
    const res = await fetch("/api/summary/latest");
    if (!res.ok) throw new Error(res.status);
    const data = await res.json();
    summary.value = data.summary;
    summaryId.value = data.summary_id;
    renderedSummary.value = DOMPurify.sanitize(marked(data.summary));
  } catch (e) {
    console.error("Summary fetch error:", e);
    summary.value = "无法加载洞察。";
    renderedSummary.value = DOMPurify.sanitize(marked(summary.value));
  }
};

const fetchNews = async (reset = false) => {
  if (loading.value) return;
  if (!reset && page.value > totalPages.value) return;

  if (reset) {
    news.value = [];
    page.value = 1;
    totalPages.value = 1;
  }

  loading.value = true;
  try {
    const params = new URLSearchParams();
    params.set("page", page.value);
    params.set("size", "20");
    if (summaryId.value) params.set("summary_id", summaryId.value);
    if (activeCategory.value) params.set("category", activeCategory.value);
    if (activeDays.value) params.set("days", activeDays.value);

    const res = await fetch(`/api/news?${params}`);
    if (!res.ok) throw new Error(res.status);
    const data = await res.json();
    news.value = reset ? data.items : [...news.value, ...data.items];
    totalPages.value = Math.ceil(data.total / data.size);
    page.value++;
  } catch (e) {
    console.error("News fetch error:", e);
  } finally {
    loading.value = false;
    firstLoad.value = false;
  }
};

// ─── 筛选 ─────────────────────────────────────────────────────
const setCategory = (cat) => {
  activeCategory.value = cat;
  fetchNews(true);
};

const onFilterChange = () => {
  fetchNews(true);
};

// ─── 滚动 ─────────────────────────────────────────────────────
const handleScroll = () => {
  const container = newsViewContainer.value?.parentElement;
  if (!container) return;
  const { scrollTop, scrollHeight, clientHeight } = container;
  showRocket.value = scrollTop > 200;
  if (scrollTop + clientHeight >= scrollHeight - 300 && !loading.value && page.value <= totalPages.value) {
    fetchNews();
  }
};

const scrollToTop = () => {
  const container = newsViewContainer.value?.parentElement;
  if (container) container.scrollTo({ top: 0, behavior: "smooth" });
};

// ─── 生命周期 ─────────────────────────────────────────────────
onMounted(async () => {
  await Promise.all([fetchStats(), fetchSummary()]);
  await fetchNews();
  const container = newsViewContainer.value?.parentElement;
  if (container) container.addEventListener("scroll", handleScroll);
});

onUnmounted(() => {
  const container = newsViewContainer.value?.parentElement;
  if (container) container.removeEventListener("scroll", handleScroll);
});
</script>

<style lang="scss" scoped>
@import url("https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap");

:root {
  --primary-green: #00ff7f;
  --secondary-green: #0c6;
  --dark-bg: #0a0e0a;
  --card-bg: #0f140f;
  --border-green: rgba(0, 255, 127, 0.3);
  --glow-green: rgba(0, 255, 127, 0.6);
}

.news-view {
  font-family: "Share Tech Mono", "Courier New", monospace;
  background-color: var(--dark-bg);
  color: var(--primary-green);
  min-height: 100vh;
  padding: 20px;
  padding-bottom: 60px;
  position: relative;
}

// ─── 数据看板 ──────────────────────────────────────────────────
.dashboard {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.dash-card {
  flex: 1 1 120px;
  min-width: 110px;
  background: var(--card-bg);
  border: 1px solid var(--border-green);
  border-radius: 6px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  position: relative;
  overflow: hidden;

  &::after {
    content: "";
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--primary-green), transparent);
    opacity: 0.3;
  }

  &.wide {
    flex: 2 1 220px;
    flex-direction: row;
    align-items: center;
    gap: 12px;
  }
}

.dash-label {
  font-size: 10px;
  color: var(--secondary-green);
  letter-spacing: 1px;
  text-transform: uppercase;
  opacity: 0.7;
}

.dash-value {
  font-size: 22px;
  font-weight: 700;
  color: var(--primary-green);
  text-shadow: 0 0 8px var(--glow-green);

  &.small {
    font-size: 12px;
    font-weight: 400;
  }
}

.mini-chart {
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 40px;
  flex: 1;
}

.mini-bar {
  flex: 1;
  min-width: 6px;
  background: var(--primary-green);
  border-radius: 2px 2px 0 0;
  opacity: 0.7;
  transition: opacity 0.2s;
  box-shadow: 0 0 4px rgba(0, 255, 127, 0.3);

  &:hover {
    opacity: 1;
    box-shadow: 0 0 8px var(--glow-green);
  }
}

// ─── 洞察面板 ──────────────────────────────────────────────────
.insight-panel {
  background: linear-gradient(135deg, #0a0e0a 0%, #0f140f 100%);
  border: 1px solid var(--border-green);
  border-radius: 6px;
  margin-bottom: 16px;
  overflow: hidden;
  position: relative;

  &::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--primary-green), transparent);
    opacity: 0.6;
  }
}

.insight-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;

  &:hover {
    background: rgba(0, 255, 127, 0.04);
  }
}

.insight-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--primary-green);
  margin: 0;
  letter-spacing: 1px;
  text-shadow: 0 0 8px var(--glow-green);
}

.insight-toggle {
  font-size: 16px;
  color: var(--primary-green);
  transition: transform 0.3s ease;
  &.open {
    transform: rotate(180deg);
  }
}

.insight-body {
  padding: 0 20px 16px;
}

.insight-content {
  color: var(--secondary-green);
  line-height: 1.6;
  font-size: 12px;
  max-height: 320px;
  overflow-y: auto;

  &::-webkit-scrollbar {
    width: 4px;
  }
  &::-webkit-scrollbar-thumb {
    background: var(--border-green);
    border-radius: 2px;
  }

  :deep(h1), :deep(h2), :deep(h3), :deep(h4) {
    color: var(--primary-green);
    font-size: 13px;
    margin-top: 10px;
    margin-bottom: 6px;
    text-shadow: 0 0 6px var(--glow-green);
  }
  :deep(p) { margin-bottom: 6px; color: #6f9; }
  :deep(ul), :deep(ol) { padding-left: 16px; margin-bottom: 6px; }
  :deep(li) { margin-bottom: 3px; }
  :deep(code) {
    background: rgba(0, 255, 127, 0.1);
    padding: 1px 4px;
    border-radius: 3px;
    border: 1px solid var(--border-green);
    font-size: 11px;
  }
  :deep(a) {
    color: var(--primary-green);
    text-decoration: none;
    border-bottom: 1px dotted var(--border-green);
    &:hover { text-shadow: 0 0 6px var(--glow-green); }
  }
}

// ─── 折叠动画 ──────────────────────────────────────────────────
.fold-enter-active, .fold-leave-active {
  transition: all 0.3s ease;
  max-height: 400px;
  overflow: hidden;
}
.fold-enter-from, .fold-leave-to {
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
  opacity: 0;
}

// ─── 筛选栏 ────────────────────────────────────────────────────
.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--border-green);
}

.filter-group {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;
}

.filter-chip {
  font-family: "Share Tech Mono", monospace;
  font-size: 11px;
  padding: 4px 10px;
  border: 1px solid var(--border-green);
  border-radius: 3px;
  background: transparent;
  color: var(--secondary-green);
  cursor: pointer;
  transition: all 0.2s;
  letter-spacing: 0.5px;

  &:hover {
    border-color: var(--primary-green);
    color: var(--primary-green);
  }
  &.active {
    background: rgba(0, 255, 127, 0.15);
    border-color: var(--primary-green);
    color: var(--primary-green);
    box-shadow: 0 0 8px rgba(0, 255, 127, 0.2);
    text-shadow: 0 0 4px var(--glow-green);
  }
}

.time-select {
  font-family: "Share Tech Mono", monospace;
  font-size: 11px;
  padding: 4px 8px;
  border: 1px solid var(--border-green);
  border-radius: 3px;
  background: var(--card-bg);
  color: var(--primary-green);
  cursor: pointer;
  outline: none;

  option {
    background: #0a0e0a;
    color: var(--primary-green);
  }

  &:focus {
    border-color: var(--primary-green);
    box-shadow: 0 0 6px rgba(0, 255, 127, 0.2);
  }
}

// ─── 分类统计条 ─────────────────────────────────────────────────
.category-stats {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 6px;
  margin-bottom: 16px;
  padding: 10px 12px;
  background: var(--card-bg);
  border: 1px solid var(--border-green);
  border-radius: 6px;
}

.cat-bar-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
}

.cat-bar-label {
  font-size: 10px;
  color: var(--secondary-green);
  min-width: 42px;
  text-align: right;
}

.cat-bar-track {
  flex: 1;
  height: 6px;
  background: rgba(0, 255, 127, 0.08);
  border-radius: 3px;
  overflow: hidden;
}

.cat-bar-fill {
  height: 100%;
  background: var(--primary-green);
  border-radius: 3px;
  box-shadow: 0 0 6px rgba(0, 255, 127, 0.3);
  transition: width 0.5s ease;
}

.cat-bar-count {
  font-size: 10px;
  color: var(--primary-green);
  min-width: 20px;
  font-weight: 700;
}

// ─── 新闻卡片 ───────────────────────────────────────────────────
.news-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 14px;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
}

.news-card {
  background: var(--card-bg);
  border: 1px solid var(--border-green);
  border-radius: 6px;
  padding: 14px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;

  &::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--primary-green), transparent);
    opacity: 0;
    transition: opacity 0.3s;
  }

  &:hover {
    transform: translateY(-3px);
    border-color: var(--primary-green);
    box-shadow: 0 0 18px rgba(0, 255, 127, 0.25), 0 6px 20px rgba(0, 0, 0, 0.5);
    &::before { opacity: 1; }
  }

  &.highlighted {
    border-color: var(--primary-green);
    box-shadow: 0 0 12px rgba(0, 255, 127, 0.2), inset 0 0 15px rgba(0, 255, 127, 0.05);
    animation: glow-pulse 3s ease-in-out infinite;
  }
}

@keyframes glow-pulse {
  0%, 100% { box-shadow: 0 0 12px rgba(0, 255, 127, 0.2), inset 0 0 15px rgba(0, 255, 127, 0.05); }
  50% { box-shadow: 0 0 16px rgba(0, 255, 127, 0.3), inset 0 0 18px rgba(0, 255, 127, 0.08); }
}

.card-top {
  margin-bottom: 8px;
}

.cat-badge {
  font-size: 10px;
  padding: 2px 7px;
  border-radius: 3px;
  border: 1px solid var(--border-green);
  color: var(--secondary-green);
  background: rgba(0, 255, 127, 0.06);
  letter-spacing: 0.5px;

  &.uncategorized {
    opacity: 0.4;
  }
}

.news-title {
  font-size: 14px;
  font-weight: 700;
  margin: 0 0 8px 0;
  line-height: 1.4;

  a {
    color: var(--primary-green);
    text-decoration: none;
    text-shadow: 0 0 4px rgba(0, 255, 127, 0.3);
    transition: all 0.2s;
    &:hover {
      color: #6f9;
      text-shadow: 0 0 8px var(--glow-green);
    }
  }
}

.news-preview {
  color: #6f9;
  line-height: 1.5;
  margin: 0 0 10px 0;
  font-size: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  opacity: 0.8;
}

.news-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 8px;
  border-top: 1px solid var(--border-green);
  font-size: 11px;
}

.news-source {
  color: var(--primary-green);
  font-weight: 600;
  padding: 2px 6px;
  background: rgba(0, 255, 127, 0.1);
  border-radius: 3px;
  border: 1px solid var(--border-green);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.news-time {
  color: var(--secondary-green);
  opacity: 0.7;
}

// ─── 空 / 加载 / 返回 ──────────────────────────────────────────
.loading-indicator {
  text-align: center;
  padding: 30px 0;
}

.loading-dots {
  display: inline-flex;
  gap: 8px;
  span {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--primary-green);
    animation: dot-pulse 1.4s ease-in-out infinite;
    &:nth-child(2) { animation-delay: 0.2s; }
    &:nth-child(3) { animation-delay: 0.4s; }
  }
}

@keyframes dot-pulse {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1.1); }
}

.no-more-news {
  text-align: center;
  padding: 20px;
  color: var(--secondary-green);
  font-size: 12px;
  opacity: 0.5;
  letter-spacing: 2px;
}

.empty-state {
  text-align: center;
  padding: 60px 0;
  color: var(--secondary-green);
  .empty-icon { font-size: 40px; opacity: 0.3; margin-bottom: 12px; }
  p { font-size: 13px; }
}

.rocket-button {
  position: fixed;
  bottom: 30px;
  right: 30px;
  background: var(--card-bg);
  color: var(--primary-green);
  border: 2px solid var(--border-green);
  border-radius: 50%;
  width: 44px;
  height: 44px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 0 12px rgba(0, 255, 127, 0.3);
  z-index: 99;
  display: flex;
  align-items: center;
  justify-content: center;

  &:hover {
    background: var(--primary-green);
    color: #0a0e0a;
    transform: translateY(-4px);
    box-shadow: 0 0 20px rgba(0, 255, 127, 0.6);
  }
}
</style>
