<template>
  <div class="news-view" ref="newsViewContainer">
    <!-- 洞察板块 - 固定在顶部 -->
    <div class="insight-container" v-if="summary">
      <h2 class="insight-title">💡 市场洞察</h2>
      <div class="insight-content" v-html="renderedSummary"></div>
    </div>

    <!-- 新闻网格流 -->
    <div class="news-grid">
      <div class="news-card" :class="{ highlighted: item.highlighted }" v-for="item in news" :key="item.url">
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
    <div v-if="loading" class="loading-indicator">正在加载...</div>
    <div v-if="!loading && page > totalPages" class="no-more-news">- 没有更多了 -</div>

    <!-- 返回顶部按钮 -->
    <button @click="scrollToTop" class="rocket-button" v-show="showRocket">▲</button>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

const newsViewContainer = ref(null);
const summary = ref(null);
const summaryId = ref(null);
const renderedSummary = ref('');
const news = ref([]);
const loading = ref(false);
const page = ref(1);
const totalPages = ref(1);
const showRocket = ref(false);

const fetchSummary = async () => {
  try {
    const response = await fetch('/api/summary/latest');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    summary.value = data.summary;
    summaryId.value = data.summary_id;
    renderedSummary.value = DOMPurify.sanitize(marked(data.summary));
  } catch (error) {
    console.error('Error fetching summary:', error);
    summary.value = '无法加载洞察。请检查后端服务。'
    renderedSummary.value = DOMPurify.sanitize(marked(summary.value));
  }
};

const fetchNews = async () => {
  if (loading.value || page.value > totalPages.value) return;
  loading.value = true;
  try {
    const url = summaryId.value 
      ? `/api/news?page=${page.value}&size=20&summary_id=${summaryId.value}`
      : `/api/news?page=${page.value}&size=20`;
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    news.value = [...news.value, ...data.items];
    totalPages.value = Math.ceil(data.total / data.size);
    page.value++;
  } catch (error) {
    console.error('Error fetching news:', error);
  } finally {
    loading.value = false;
  }
};

const handleScroll = () => {
  // 监听父容器 (.content-area) 的滚动
  const container = newsViewContainer.value?.parentElement;
  if (container) {
    const { scrollTop, scrollHeight, clientHeight } = container;
    // Show rocket button if scrolled down enough
    showRocket.value = scrollTop > 200; 
    if (scrollTop + clientHeight >= scrollHeight - 300 && !loading.value && page.value <= totalPages.value) {
      fetchNews();
    }
  }
};

const scrollToTop = () => {
  // 滚动父容器到顶部
  const container = newsViewContainer.value?.parentElement;
  if (container) {
    container.scrollTo({ top: 0, behavior: 'smooth' });
  }
};

const formatTime = (timeStr) => {
  return new Date(timeStr).toLocaleString('zh-CN');
};

onMounted(async () => {
  // 先获取summary，然后再获取news（这样news才能知道哪些需要高亮）
  await fetchSummary();
  await fetchNews();
  // 监听父容器的滚动事件
  const container = newsViewContainer.value?.parentElement;
  if (container) {
    container.addEventListener('scroll', handleScroll);
  }
});

onUnmounted(() => {
  const container = newsViewContainer.value?.parentElement;
  if (container) {
    container.removeEventListener('scroll', handleScroll);
  }
});
</script>

<style lang="scss" scoped>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');:root{--primary-green:#00ff7f;--secondary-green:#0c6;--dark-bg:#0a0e0a;--card-bg:#0f140f;--border-green:rgba(0,255,127,.3);--glow-green:rgba(0,255,127,.6)}.news-view{font-family:'Share Tech Mono','Courier New',monospace;background-color:var(--dark-bg);color:var(--primary-green);min-height:100vh;position:relative;padding-left:0;padding-bottom:40px;&::-webkit-scrollbar{width:6px}&::-webkit-scrollbar-track{background:#0a0e0a}&::-webkit-scrollbar-thumb{background:var(--border-green);border-radius:3px;&:hover{background:var(--primary-green);box-shadow:0 0 8px var(--glow-green)}}}.insight-container{position:fixed;top:0;left:220px;right:0;background:linear-gradient(135deg,#0a0e0a 0,#0f140f 100%);border-bottom:2px solid var(--border-green);padding:16px 32px;box-shadow:0 0 20px rgba(0,255,127,.1),0 4px 16px rgba(0,0,0,.8);z-index:50;max-height:200px;overflow-y:auto;overflow-x:hidden;&::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent 0,var(--primary-green) 50%,transparent 100%);box-shadow:0 0 10px var(--glow-green);animation:oscilloscope-scan 4s linear infinite;opacity:.6;z-index:1;pointer-events:none}&::after{content:'';position:absolute;top:0;left:0;right:0;bottom:0;background:repeating-linear-gradient(90deg,transparent,transparent 2px,rgba(0,255,127,.03) 2px,rgba(0,255,127,.03) 4px);background-size:40px 100%;animation:wave-move 20s linear infinite;pointer-events:none;z-index:0}.insight-title,.insight-content{position:relative;z-index:2}&::-webkit-scrollbar{width:4px}&::-webkit-scrollbar-track{background:#0a0e0a}&::-webkit-scrollbar-thumb{background:var(--border-green);border-radius:2px;&:hover{background:var(--primary-green);box-shadow:0 0 6px var(--glow-green)}}}@keyframes oscilloscope-scan{0%{top:0;opacity:0}5%,95%{opacity:.8}100%{top:calc(100% - 2px);opacity:0}}@keyframes wave-move{0%{background-position:0 0}100%{background-position:40px 0}}.insight-title{font-size:14px;font-weight:700;color:var(--primary-green);margin:0 0 8px 0;padding-bottom:6px;border-bottom:1px solid var(--border-green);letter-spacing:1px;text-shadow:0 0 8px var(--glow-green);text-transform:uppercase}.insight-content{color:var(--secondary-green);line-height:1.5;font-size:12px;h1,h2,h3,h4,h5,h6{color:var(--primary-green);margin-top:8px;margin-bottom:6px;font-weight:700;font-size:13px;text-shadow:0 0 6px var(--glow-green)}p{margin-bottom:6px;color:#6f9}ul,ol{margin-bottom:6px;padding-left:16px}li{margin-bottom:3px}code{background:rgba(0,255,127,.1);padding:1px 4px;border-radius:3px;border:1px solid var(--border-green);font-family:'Share Tech Mono',monospace;font-size:11px;color:var(--primary-green)}pre{background:#0a0e0a;border:1px solid var(--border-green);padding:6px;border-radius:4px;overflow-x:auto;margin-bottom:6px;code{background:none;padding:0;border:none}}a{color:var(--primary-green);text-decoration:none;border-bottom:1px dotted var(--border-green);transition:all .2s;&:hover{color:#6f9;text-shadow:0 0 6px var(--glow-green);border-bottom-style:solid}}}.news-grid{margin-top:220px;padding:20px;display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px;grid-auto-flow:row;@media(max-width:1400px){grid-template-columns:repeat(auto-fill,minmax(250px,1fr))}@media(max-width:1000px){grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}@media(max-width:768px){grid-template-columns:1fr}}.news-card{background:var(--card-bg);border:1px solid var(--border-green);border-radius:6px;padding:16px;transition:all .3s ease;cursor:pointer;position:relative;overflow:hidden;&::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,var(--primary-green),transparent);opacity:0;transition:opacity .3s}&:hover{transform:translateY(-4px);box-shadow:0 0 20px rgba(0,255,127,.3),0 8px 24px rgba(0,0,0,.5),inset 0 0 40px rgba(0,255,127,.05);border-color:var(--primary-green);&::before{opacity:1}}&.highlighted{border:1.5px solid var(--primary-green);box-shadow:0 0 12px rgba(0,255,127,.25),0 0 20px rgba(0,255,127,.12),inset 0 0 15px rgba(0,255,127,.06);animation:glow-pulse 3s ease-in-out infinite;&::before{opacity:.6}&:hover{box-shadow:0 0 18px rgba(0,255,127,.35),0 0 30px rgba(0,255,127,.18),0 8px 24px rgba(0,0,0,.5),inset 0 0 20px rgba(0,255,127,.08);&::before{opacity:1}}}}@keyframes glow-pulse{0%,100%{box-shadow:0 0 12px rgba(0,255,127,.25),0 0 20px rgba(0,255,127,.12),inset 0 0 15px rgba(0,255,127,.06)}50%{box-shadow:0 0 16px rgba(0,255,127,.32),0 0 28px rgba(0,255,127,.16),inset 0 0 18px rgba(0,255,127,.08)}}.news-title{font-size:15px;font-weight:700;margin:0 0 10px 0;line-height:1.4;a{color:var(--primary-green);text-decoration:none;transition:all .2s;text-shadow:0 0 4px rgba(0,255,127,.3);&:hover{color:#6f9;text-shadow:0 0 8px var(--glow-green)}}}.news-preview{color:#6f9;line-height:1.5;margin:0 0 10px 0;font-size:12px;display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden;opacity:.85}.news-meta{display:flex;justify-content:space-between;align-items:center;padding-top:10px;border-top:1px solid var(--border-green);font-size:11px}.news-source{color:var(--primary-green);font-weight:600;padding:3px 8px;background:rgba(0,255,127,.1);border-radius:3px;border:1px solid var(--border-green);text-shadow:0 0 4px rgba(0,255,127,.3);text-transform:uppercase;letter-spacing:.5px}.news-time{color:var(--secondary-green);font-family:'Share Tech Mono',monospace;opacity:.7}.loading-indicator,.no-more-news{text-align:center;padding:20px;color:var(--secondary-green);font-size:13px;margin-top:20px;text-shadow:0 0 6px rgba(0,255,127,.3);letter-spacing:2px}.loading-indicator{animation:pulse 1.5s ease-in-out infinite}@keyframes pulse{0%,100%{opacity:.6}50%{opacity:1}}.rocket-button{position:fixed;bottom:30px;right:30px;background:var(--card-bg);color:var(--primary-green);border:2px solid var(--border-green);border-radius:50%;width:50px;height:50px;font-size:1.2rem;cursor:pointer;transition:all .3s ease;box-shadow:0 0 15px rgba(0,255,127,.3),0 4px 12px rgba(0,0,0,.5);z-index:99;font-weight:700;display:flex;align-items:center;justify-content:center;line-height:1;&:hover{background:var(--primary-green);color:#0a0e0a;transform:translateY(-5px);box-shadow:0 0 25px rgba(0,255,127,.6),0 6px 16px rgba(0,0,0,.6);border-color:var(--primary-green)}&:active{transform:translateY(-2px)}}
</style>

