<template>
  <div class="skins-view" ref="skinsContainer">
    <!-- 顶部搜索栏 -->
    <div class="search-bar">
      <span class="search-icon">🔍</span>
      <input
        v-model="searchQuery"
        class="search-input"
        placeholder="搜索饰品 (如: AK-47, Hyper Beast, 蝴蝶刀...)"
        @input="onSearchInput"
        @keydown.enter="doSearch"
        autocomplete="off"
        spellcheck="false"
      />
      <span v-if="searchQuery" class="clear-btn" @click="clearSearch">✕</span>
    </div>

    <!-- 标题栏 -->
    <div class="section-header">
      <h2 class="section-title">
        <span class="icon">◈</span>
        {{ isSearching ? `搜索结果 "${searchQuery}"` : "🔥 热门饰品" }}
      </h2>
      <span class="badge">{{ items.length }} 个</span>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-panel">
      <div class="loading-dots"><span></span><span></span><span></span></div>
      <p>正在加载...</p>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!loading && items.length === 0" class="empty-state">
      <div class="empty-icon">⬡</div>
      <p>{{ isSearching ? "未找到匹配的饰品" : "暂无饰品数据" }}</p>
      <p class="empty-hint" v-if="!isSearching">
        运行 Orchestrator 流水线后将自动填充数据
      </p>
    </div>

    <!-- 饰品卡片网格 -->
    <div v-else class="skins-grid">
      <div
        v-for="item in items"
        :key="item.id"
        class="skin-card"
        :class="{ 'has-price': item.current_price }"
        @click="openDetail(item)"
      >
        <div class="card-header">
          <span class="weapon-type-badge" :class="item.weapon_type || 'other'">
            {{ weaponTypeLabel(item.weapon_type) }}
          </span>
          <span class="mention-count" title="被提及次数"
            >✦ {{ item.mention_count }}</span
          >
        </div>

        <h3 class="skin-name">{{ item.skin_name }}</h3>
        <p
          class="skin-hash"
          v-if="
            item.market_hash_name && item.market_hash_name !== item.skin_name
          "
        >
          {{ item.market_hash_name }}
        </p>

        <div class="skin-price-row" v-if="item.current_price">
          <span class="price">¥{{ formatPrice(item.current_price) }}</span>
          <span
            class="price-change"
            :class="priceChangeClass(item.price_change_24h)"
          >
            {{ formatChange(item.price_change_24h) }}
          </span>
        </div>
        <div class="skin-price-row no-price" v-else>
          <span class="price-na">暂无价格</span>
          <button
            class="goto-items-btn"
            @click.stop="
              router.push({
                path: '/items',
                query: { search: item.market_hash_name },
              })
            "
          >
            查看价格 →
          </button>
        </div>

        <div class="card-footer">
          <span class="last-updated">{{ formatTime(item.last_updated) }}</span>
        </div>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <transition name="modal-fade">
      <div v-if="selectedItem" class="modal-overlay" @click.self="closeDetail">
        <div class="modal-box">
          <button class="modal-close" @click="closeDetail">✕</button>

          <div class="modal-header">
            <span
              class="weapon-type-badge large"
              :class="selectedItem.entity?.weapon_type || 'other'"
            >
              {{ weaponTypeLabel(selectedItem.entity?.weapon_type) }}
            </span>
            <h2 class="modal-title">{{ selectedItem.entity?.skin_name }}</h2>
            <p class="modal-hash" v-if="selectedItem.entity?.market_hash_name">
              {{ selectedItem.entity?.market_hash_name }}
            </p>
          </div>

          <div class="modal-stats">
            <div class="stat-item">
              <span class="stat-label">提及次数</span>
              <span class="stat-value">{{
                selectedItem.entity?.mention_count
              }}</span>
            </div>
            <div class="stat-item" v-if="selectedItem.entity?.rarity">
              <span class="stat-label">稀有度</span>
              <span class="stat-value">{{ selectedItem.entity.rarity }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">首次发现</span>
              <span class="stat-value">{{
                formatTime(selectedItem.entity?.first_seen)
              }}</span>
            </div>
          </div>

          <!-- 价格详情 -->
          <div
            v-if="selectedItem.details && selectedItem.details.length > 0"
            class="price-details"
          >
            <h3 class="section-sub-title">价格数据</h3>
            <div
              v-for="d in selectedItem.details"
              :key="d.id"
              class="price-detail-row"
            >
              <span class="platform-badge">{{ d.platform }}</span>
              <span class="detail-price" v-if="d.current_price"
                >¥{{ formatPrice(d.current_price) }}</span
              >
              <span class="detail-price no-price" v-else>—</span>
              <span
                class="detail-change"
                :class="priceChangeClass(d.price_change_24h)"
                v-if="d.price_change_24h != null"
              >
                24h {{ formatChange(d.price_change_24h) }}
              </span>
              <span
                class="detail-change"
                :class="priceChangeClass(d.price_change_7d)"
                v-if="d.price_change_7d != null"
              >
                7d {{ formatChange(d.price_change_7d) }}
              </span>
              <span class="detail-update"
                >更新于 {{ formatTime(d.last_crawled_at) }}</span
              >
            </div>
          </div>
          <div v-else class="no-price-detail">
            <p>暂无价格数据，等待 Investigator Agent 爬取...</p>
            <button
              v-if="selectedItem.entity?.market_hash_name"
              class="action-btn goto-items"
              @click="
                router.push({
                  path: '/items',
                  query: { search: selectedItem.entity.market_hash_name },
                })
              "
            >
              📦 在饰品页查看价格
            </button>
          </div>

          <!-- steamdt 外链 -->
          <div class="modal-actions">
            <a
              v-if="selectedItem.entity?.market_hash_name"
              :href="`https://steamdt.com/mkt?search=${encodeURIComponent(selectedItem.entity.market_hash_name)}`"
              target="_blank"
              class="action-btn"
            >
              ↗ 在 SteamDT 查看
            </a>
            <a
              v-if="selectedItem.entity?.market_hash_name"
              :href="`https://buff.163.com/market/csgo#tab=selling&page_num=1&search=${encodeURIComponent(selectedItem.entity.market_hash_name)}`"
              target="_blank"
              class="action-btn secondary"
            >
              ↗ 在 BUFF 查看
            </a>
            <button
              v-if="selectedItem.entity?.market_hash_name"
              class="action-btn goto-items"
              @click="
                router.push({
                  path: '/items',
                  query: { search: selectedItem.entity.market_hash_name },
                })
              "
            >
              📦 在饰品页查看价格
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import api from "@/services/api";

const router = useRouter();
const skinsContainer = ref(null);
const items = ref([]);
const loading = ref(false);
const searchQuery = ref("");
const isSearching = ref(false);
const selectedItem = ref(null);

let searchTimer = null;

const weaponTypeLabel = (type) => {
  const map = {
    knife: "刀",
    glove: "手套",
    rifle: "步枪",
    pistol: "手枪",
    smg: "冲锋枪",
    shotgun: "霰弹枪",
    machinegun: "机枪",
    other: "其他",
  };
  return map[type] || "其他";
};

const formatPrice = (val) => {
  if (val == null) return "—";
  return Number(val).toLocaleString("zh-CN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
};

const formatChange = (val) => {
  if (val == null) return "";
  const pct = (Number(val) * 100).toFixed(2);
  return pct >= 0 ? `+${pct}%` : `${pct}%`;
};

const priceChangeClass = (val) => {
  if (val == null) return "";
  return Number(val) >= 0 ? "positive" : "negative";
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

const loadTrending = async () => {
  loading.value = true;
  const res = await api.getTrendingSkins(40);
  loading.value = false;
  if (res.success) {
    items.value = res.items || [];
  } else {
    items.value = [];
  }
};

const doSearch = async () => {
  const q = searchQuery.value.trim();
  if (!q) {
    isSearching.value = false;
    await loadTrending();
    return;
  }
  loading.value = true;
  isSearching.value = true;
  const res = await api.searchSkins(q, 40);
  loading.value = false;
  items.value = res.success ? res.items || [] : [];
};

const onSearchInput = () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    doSearch();
  }, 400);
};

const clearSearch = () => {
  searchQuery.value = "";
  isSearching.value = false;
  loadTrending();
};

const openDetail = async (item) => {
  const res = await api.getSkinDetail(item.id);
  if (res.success) {
    selectedItem.value = res;
  } else {
    // 降级展示基本信息
    selectedItem.value = { entity: item, details: [] };
  }
};

const closeDetail = () => {
  selectedItem.value = null;
};

onMounted(() => {
  loadTrending();
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

.skins-view {
  font-family: "Share Tech Mono", "Courier New", monospace;
  background-color: var(--dark-bg);
  color: var(--primary-green);
  min-height: 100vh;
  padding: 20px;
  position: relative;
}

// ─── 搜索栏 ──────────────────────────────────────────────────────
.search-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--card-bg);
  border: 1px solid var(--border-green);
  border-radius: 6px;
  padding: 10px 16px;
  margin-bottom: 20px;
  box-shadow: 0 0 12px rgba(0, 255, 127, 0.08);

  &:focus-within {
    border-color: var(--primary-green);
    box-shadow: 0 0 16px rgba(0, 255, 127, 0.2);
  }
}

.search-icon {
  font-size: 16px;
  opacity: 0.7;
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--primary-green);
  font-family: "Share Tech Mono", monospace;
  font-size: 14px;
  caret-color: var(--primary-green);

  &::placeholder {
    color: rgba(0, 255, 127, 0.35);
  }
}

.clear-btn {
  cursor: pointer;
  opacity: 0.5;
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 3px;
  transition: opacity 0.2s;
  &:hover {
    opacity: 1;
  }
}

// ─── 标题栏 ──────────────────────────────────────────────────────
.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.section-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--primary-green);
  margin: 0;
  letter-spacing: 1px;
  text-shadow: 0 0 8px var(--glow-green);

  .icon {
    margin-right: 6px;
  }
}

.badge {
  font-size: 11px;
  padding: 2px 8px;
  background: rgba(0, 255, 127, 0.1);
  border: 1px solid var(--border-green);
  border-radius: 10px;
  color: var(--secondary-green);
}

// ─── 加载 / 空状态 ─────────────────────────────────────────────
.loading-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 0;
  color: var(--secondary-green);
  font-size: 13px;
  letter-spacing: 2px;
}

.loading-dots {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;

  span {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--primary-green);
    animation: dot-pulse 1.4s ease-in-out infinite;

    &:nth-child(2) {
      animation-delay: 0.2s;
    }
    &:nth-child(3) {
      animation-delay: 0.4s;
    }
  }
}

@keyframes dot-pulse {
  0%,
  80%,
  100% {
    opacity: 0.3;
    transform: scale(0.8);
  }
  40% {
    opacity: 1;
    transform: scale(1.1);
  }
}

.empty-state {
  text-align: center;
  padding: 80px 0;
  color: var(--secondary-green);

  .empty-icon {
    font-size: 48px;
    opacity: 0.3;
    margin-bottom: 16px;
  }
  p {
    margin: 6px 0;
    font-size: 14px;
  }
  .empty-hint {
    font-size: 12px;
    opacity: 0.5;
  }
}

// ─── 卡片网格 ─────────────────────────────────────────────────
.skins-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 14px;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
}

.skin-card {
  background: var(--card-bg);
  border: 1px solid var(--border-green);
  border-radius: 6px;
  padding: 14px;
  cursor: pointer;
  transition: all 0.25s ease;
  position: relative;
  overflow: hidden;

  &::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(
      90deg,
      transparent,
      var(--primary-green),
      transparent
    );
    opacity: 0;
    transition: opacity 0.25s;
  }

  &:hover {
    transform: translateY(-3px);
    border-color: var(--primary-green);
    box-shadow:
      0 0 18px rgba(0, 255, 127, 0.25),
      0 6px 20px rgba(0, 0, 0, 0.5),
      inset 0 0 30px rgba(0, 255, 127, 0.04);
    &::before {
      opacity: 1;
    }
  }

  &.has-price {
    border-color: rgba(0, 255, 127, 0.45);
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.weapon-type-badge {
  font-size: 10px;
  padding: 2px 7px;
  border-radius: 3px;
  border: 1px solid;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  font-weight: 700;

  &.knife {
    color: #ff6b6b;
    border-color: rgba(255, 107, 107, 0.4);
    background: rgba(255, 107, 107, 0.08);
  }
  &.glove {
    color: #ffd93d;
    border-color: rgba(255, 217, 61, 0.4);
    background: rgba(255, 217, 61, 0.08);
  }
  &.rifle {
    color: #6bcbff;
    border-color: rgba(107, 203, 255, 0.4);
    background: rgba(107, 203, 255, 0.08);
  }
  &.pistol {
    color: #b8ff6b;
    border-color: rgba(184, 255, 107, 0.4);
    background: rgba(184, 255, 107, 0.08);
  }
  &.smg {
    color: #d98fff;
    border-color: rgba(217, 143, 255, 0.4);
    background: rgba(217, 143, 255, 0.08);
  }
  &.shotgun {
    color: #ff9f6b;
    border-color: rgba(255, 159, 107, 0.4);
    background: rgba(255, 159, 107, 0.08);
  }
  &.other {
    color: var(--secondary-green);
    border-color: var(--border-green);
    background: rgba(0, 255, 127, 0.05);
  }

  &.large {
    font-size: 12px;
    padding: 3px 10px;
  }
}

.mention-count {
  font-size: 11px;
  color: var(--secondary-green);
  opacity: 0.7;
}

.skin-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--primary-green);
  margin: 0 0 4px 0;
  text-shadow: 0 0 4px rgba(0, 255, 127, 0.3);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.skin-hash {
  font-size: 11px;
  color: var(--secondary-green);
  opacity: 0.6;
  margin: 0 0 10px 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.skin-price-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 10px;
}

.price {
  font-size: 16px;
  font-weight: 700;
  color: var(--primary-green);
  text-shadow: 0 0 8px rgba(0, 255, 127, 0.4);
}

.price-change {
  font-size: 11px;
  font-weight: 600;
  &.positive {
    color: #00ff7f;
  }
  &.negative {
    color: #ff6b6b;
  }
}

.price-na {
  font-size: 12px;
  color: rgba(0, 255, 127, 0.3);
}

.card-footer {
  padding-top: 8px;
  border-top: 1px solid var(--border-green);
}

.last-updated {
  font-size: 10px;
  color: var(--secondary-green);
  opacity: 0.5;
}

// ─── 弹窗 ─────────────────────────────────────────────────────
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.85);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  backdrop-filter: blur(4px);
}

.modal-box {
  background: #0d1a0d;
  border: 1px solid var(--primary-green);
  border-radius: 8px;
  padding: 28px;
  width: 100%;
  max-width: 560px;
  max-height: 80vh;
  overflow-y: auto;
  position: relative;
  box-shadow:
    0 0 40px rgba(0, 255, 127, 0.2),
    0 20px 60px rgba(0, 0, 0, 0.8);

  &::-webkit-scrollbar {
    width: 4px;
  }
  &::-webkit-scrollbar-track {
    background: #0a0e0a;
  }
  &::-webkit-scrollbar-thumb {
    background: var(--border-green);
    border-radius: 2px;
  }
}

.modal-close {
  position: absolute;
  top: 14px;
  right: 14px;
  background: transparent;
  border: 1px solid var(--border-green);
  color: var(--primary-green);
  width: 28px;
  height: 28px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
  &:hover {
    background: rgba(0, 255, 127, 0.1);
    border-color: var(--primary-green);
  }
}

.modal-header {
  margin-bottom: 20px;
  .modal-title {
    font-size: 20px;
    font-weight: 700;
    color: var(--primary-green);
    margin: 8px 0 4px 0;
    text-shadow: 0 0 10px var(--glow-green);
  }
  .modal-hash {
    font-size: 12px;
    color: var(--secondary-green);
    opacity: 0.6;
    margin: 0;
  }
}

.modal-stats {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  padding: 14px 0;
  border-top: 1px solid var(--border-green);
  border-bottom: 1px solid var(--border-green);
  margin-bottom: 20px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.stat-label {
  font-size: 10px;
  color: var(--secondary-green);
  opacity: 0.6;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.stat-value {
  font-size: 14px;
  color: var(--primary-green);
  font-weight: 700;
}

.section-sub-title {
  font-size: 12px;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--secondary-green);
  opacity: 0.7;
  margin: 0 0 12px 0;
}

.price-details {
  margin-bottom: 20px;
}

.price-detail-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: rgba(0, 255, 127, 0.04);
  border: 1px solid var(--border-green);
  border-radius: 4px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.platform-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border: 1px solid rgba(107, 203, 255, 0.4);
  color: #6bcbff;
  border-radius: 3px;
  background: rgba(107, 203, 255, 0.07);
  min-width: 52px;
  text-align: center;
}

.detail-price {
  font-size: 15px;
  font-weight: 700;
  color: var(--primary-green);
  text-shadow: 0 0 6px rgba(0, 255, 127, 0.3);
  &.no-price {
    color: rgba(0, 255, 127, 0.3);
    font-size: 13px;
  }
}

.detail-change {
  font-size: 11px;
  font-weight: 600;
  &.positive {
    color: #00ff7f;
  }
  &.negative {
    color: #ff6b6b;
  }
}

.detail-update {
  margin-left: auto;
  font-size: 10px;
  color: var(--secondary-green);
  opacity: 0.5;
}

.no-price-detail {
  padding: 20px;
  text-align: center;
  color: rgba(0, 255, 127, 0.4);
  font-size: 12px;
  border: 1px dashed var(--border-green);
  border-radius: 4px;
  margin-bottom: 20px;
  letter-spacing: 0.5px;
}

.modal-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.action-btn {
  display: inline-block;
  padding: 8px 16px;
  border: 1px solid var(--border-green);
  color: var(--primary-green);
  text-decoration: none;
  font-size: 12px;
  border-radius: 4px;
  transition: all 0.2s;
  background: rgba(0, 255, 127, 0.05);

  &:hover {
    background: rgba(0, 255, 127, 0.12);
    border-color: var(--primary-green);
    box-shadow: 0 0 10px rgba(0, 255, 127, 0.2);
  }

  &.secondary {
    color: #6bcbff;
    border-color: rgba(107, 203, 255, 0.35);
    background: rgba(107, 203, 255, 0.05);
    &:hover {
      background: rgba(107, 203, 255, 0.12);
      border-color: #6bcbff;
      box-shadow: 0 0 10px rgba(107, 203, 255, 0.2);
    }
  }

  &.goto-items {
    color: #ffa500;
    border-color: rgba(255, 165, 0, 0.35);
    background: rgba(255, 165, 0, 0.05);
    cursor: pointer;
    &:hover {
      background: rgba(255, 165, 0, 0.12);
      border-color: #ffa500;
      box-shadow: 0 0 10px rgba(255, 165, 0, 0.2);
    }
  }
}

.goto-items-btn {
  padding: 2px 8px;
  font-size: 11px;
  color: #ffa500;
  background: rgba(255, 165, 0, 0.08);
  border: 1px solid rgba(255, 165, 0, 0.35);
  border-radius: 3px;
  cursor: pointer;
  transition: all 0.2s;
  font-family: "Share Tech Mono", "Courier New", monospace;
  &:hover {
    background: rgba(255, 165, 0, 0.15);
    border-color: #ffa500;
    box-shadow: 0 0 6px rgba(255, 165, 0, 0.3);
  }
}

// ─── 过渡动画 ─────────────────────────────────────────────────
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
