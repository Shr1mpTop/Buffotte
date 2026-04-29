<template>
  <div class="trade-notes-page">
    <header class="tn-header">
      <div>
        <div class="tn-title">买卖笔记</div>
        <div class="tn-sub">POSITION LEDGER / BUY SELL JOURNAL</div>
      </div>
      <button class="ghost-btn" @click="refreshAll" :disabled="loading">
        刷新
      </button>
    </header>

    <section class="summary-strip">
      <div class="summary-cell">
        <span>当前仓位</span>
        <strong>{{ fmtQty(totalSummary.remainingQty) }} 件 / ¥{{ fmtMoney(totalSummary.remainingCost) }}</strong>
      </div>
      <div class="summary-cell">
        <span>已实现盈亏</span>
        <strong :class="profitClass(totalSummary.realizedProfit)">
          ¥{{ fmtMoney(totalSummary.realizedProfit) }}
        </strong>
      </div>
      <div class="summary-cell">
        <span>总买入</span>
        <strong>¥{{ fmtMoney(totalSummary.buyCost) }}</strong>
      </div>
      <div class="summary-cell">
        <span>总卖出到账</span>
        <strong>¥{{ fmtMoney(totalSummary.sellNet) }}</strong>
      </div>
    </section>

    <div class="tn-grid">
      <aside class="panel positions-panel">
        <div class="panel-hd">
          <span class="pc-dot"></span>
          当前仓位
          <span class="count-pill">{{ openPositions.length }}</span>
        </div>
        <div v-if="loading" class="empty-line">正在加载...</div>
        <div v-else-if="!openPositions.length" class="empty-line">暂无当前持仓</div>
        <button
          v-for="position in openPositions"
          :key="position.market_hash_name"
          class="position-row"
          :class="{ selected: selectedMarket === position.market_hash_name }"
          @click="selectPosition(position)"
        >
          <span class="pr-name">{{ position.item_name || position.market_hash_name }}</span>
          <span class="pr-meta">
            持 {{ fmtQty(position.remaining_quantity) }}
            <b :class="profitClass(position.realized_profit)">
              ¥{{ fmtMoney(position.realized_profit) }}
            </b>
          </span>
        </button>
        <div v-if="closedPositions.length" class="position-section-title">
          <span>已清仓记录</span>
          <span>{{ closedPositions.length }}</span>
        </div>
        <button
          v-for="position in closedPositions"
          :key="`closed-${position.market_hash_name}`"
          class="position-row closed"
          :class="{ selected: selectedMarket === position.market_hash_name }"
          @click="selectPosition(position)"
        >
          <span class="pr-name">{{ position.item_name || position.market_hash_name }}</span>
          <span class="pr-meta">
            清仓 {{ fmtQty(position.sell_quantity) }}
            <b :class="profitClass(position.realized_profit)">
              ¥{{ fmtMoney(position.realized_profit) }}
            </b>
          </span>
        </button>
      </aside>

      <main class="workspace">
        <section class="panel search-panel">
          <div class="panel-hd">
            <span class="pc-dot"></span>
            选择饰品
          </div>
          <div class="search-row">
            <input
              v-model="searchQuery"
              class="field"
              placeholder="输入饰品名称或 market hash..."
              @input="scheduleSearch"
              @keydown.enter.prevent="searchNow"
            />
            <button class="action-btn" @click="searchNow" :disabled="searching">搜索</button>
          </div>
          <div v-if="searchResults.length" class="result-list">
            <button
              v-for="item in searchResults"
              :key="item.market_hash_name || item.id"
              class="result-row"
              @click="pickItem(item)"
            >
              <span>{{ item.name || item.market_hash_name }}</span>
              <small>{{ item.market_hash_name }}</small>
            </button>
          </div>
        </section>

        <section class="panel editor-panel">
          <div class="panel-hd">
            <span class="pc-dot"></span>
            记录流水
          </div>
          <div class="selected-item">
            <span>{{ form.item_name || form.market_hash_name || '未选择饰品' }}</span>
            <small v-if="form.market_hash_name">{{ form.market_hash_name }}</small>
          </div>
          <div class="form-grid">
            <div class="segmented">
              <button :class="{ active: form.side === 'BUY' }" @click="form.side = 'BUY'">买入</button>
              <button :class="{ active: form.side === 'SELL' }" @click="form.side = 'SELL'">卖出</button>
            </div>
            <label>
              <span>平台</span>
              <select v-model="form.platform" class="field">
                <option v-for="fee in platformFees" :key="fee.platform_name" :value="fee.platform_name">
                  {{ fee.display_name || fee.platform_name }}
                </option>
              </select>
            </label>
            <label>
              <span>日期</span>
              <input v-model="form.trade_date" type="date" class="field" />
            </label>
            <label>
              <span>数量</span>
              <input v-model.number="form.quantity" type="number" min="0" step="0.0001" class="field" />
            </label>
            <label>
              <span>单价</span>
              <input v-model.number="form.unit_price" type="number" min="0" step="0.01" class="field" />
            </label>
            <label class="note-field">
              <span>备注</span>
              <input v-model="form.note" class="field" placeholder="磨损、贴纸、订单号..." />
            </label>
          </div>
          <div class="calc-strip">
            <span>成交额 ¥{{ fmtMoney(preview.gross) }}</span>
            <span v-if="form.side === 'SELL'">可卖 {{ fmtQty(currentRemainingQuantity) }}</span>
            <span v-if="form.side === 'SELL'">交易费 ¥{{ fmtMoney(preview.sellFee) }}</span>
            <span v-if="form.side === 'SELL'">提现费 ¥{{ fmtMoney(preview.withdrawFee) }}</span>
            <strong :class="form.side === 'SELL' ? profitClass(preview.net) : ''">
              {{ form.side === 'SELL' ? '到账' : '成本' }} ¥{{ fmtMoney(preview.net) }}
            </strong>
          </div>
          <button class="submit-btn" @click="submitEntry" :disabled="saving || !canSubmit">
            {{ form.side === 'BUY' ? '记录买入' : '记录卖出' }}
          </button>
          <div v-if="sellQuantityError" class="hint-line">
            卖出数量超过当前持仓 {{ fmtQty(currentRemainingQuantity) }}
          </div>
          <div v-if="error" class="error-line">{{ error }}</div>
        </section>

        <section class="panel detail-panel">
          <div class="panel-hd">
            <span class="pc-dot"></span>
            明细
          </div>
          <div v-if="selectedPosition" class="position-summary">
            <div><span>买入数量</span><b>{{ fmtQty(selectedPosition.buy_quantity) }}</b></div>
            <div><span>卖出数量</span><b>{{ fmtQty(selectedPosition.sell_quantity) }}</b></div>
            <div><span>当前持仓</span><b>{{ fmtQty(selectedPosition.remaining_quantity) }}</b></div>
            <div><span>均价</span><b>¥{{ fmtMoney(selectedPosition.average_cost) }}</b></div>
            <div><span>持仓成本</span><b>¥{{ fmtMoney(selectedPosition.remaining_cost) }}</b></div>
            <div>
              <span>已实现盈亏</span>
              <b :class="profitClass(selectedPosition.realized_profit)">
                ¥{{ fmtMoney(selectedPosition.realized_profit) }}
              </b>
            </div>
          </div>
          <div class="entry-table" v-if="entries.length">
            <div class="entry-head">
              <span>日期</span><span>方向</span><span>平台</span><span>数量</span>
              <span>单价</span><span>费用</span><span>净额</span><span></span>
            </div>
            <div v-for="entry in entries" :key="entry.id" class="entry-row">
              <span>{{ entry.trade_date }}</span>
              <span :class="entry.side === 'SELL' ? 'profit-negative' : 'profit-positive'">
                {{ entry.side === 'SELL' ? '卖' : '买' }}
              </span>
              <span>{{ platformName(entry.platform) }}</span>
              <span>{{ fmtQty(entry.quantity) }}</span>
              <span>¥{{ fmtMoney(entry.unit_price) }}</span>
              <span>¥{{ fmtMoney(entry.sell_fee + entry.withdraw_fee) }}</span>
              <span :class="Number(entry.net_amount || 0) >= 0 ? 'profit-positive' : 'profit-negative'">
                ¥{{ fmtMoney(entry.net_amount) }}
              </span>
              <button class="mini-btn" @click="deleteEntry(entry)">删</button>
            </div>
          </div>
          <div v-else class="empty-line">选择或新增一条记录后查看明细</div>
        </section>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import api from '../services/api';

const user = ref(JSON.parse(localStorage.getItem('user')));
const positions = ref([]);
const entries = ref([]);
const selectedMarket = ref(null);
const platformFees = ref([]);
const searchQuery = ref('');
const searchResults = ref([]);
const loading = ref(false);
const searching = ref(false);
const saving = ref(false);
const error = ref('');
let searchTimer = null;

const today = () => new Date().toISOString().slice(0, 10);

const form = reactive({
  market_hash_name: '',
  item_name: '',
  side: 'BUY',
  platform: 'BUFF',
  trade_date: today(),
  quantity: 1,
  unit_price: null,
  note: '',
});

const selectedPosition = computed(() =>
  positions.value.find((item) => item.market_hash_name === selectedMarket.value) || null
);

const openPositions = computed(() =>
  positions.value.filter((item) => Number(item.remaining_quantity || 0) > 0)
);

const closedPositions = computed(() =>
  positions.value.filter((item) =>
    Number(item.buy_quantity || 0) > 0 && Number(item.remaining_quantity || 0) <= 0
  )
);

const currentRemainingQuantity = computed(() => Number(selectedPosition.value?.remaining_quantity || 0));

const totalSummary = computed(() => positions.value.reduce((acc, item) => {
  acc.remainingQty += Math.max(Number(item.remaining_quantity || 0), 0);
  acc.remainingCost += Number(item.remaining_cost || 0);
  acc.realizedProfit += Number(item.realized_profit || 0);
  acc.buyCost += Number(item.buy_cost || 0);
  acc.sellNet += Number(item.sell_net || 0);
  return acc;
}, { remainingQty: 0, remainingCost: 0, realizedProfit: 0, buyCost: 0, sellNet: 0 }));

const feeConfig = computed(() =>
  platformFees.value.find((fee) => fee.platform_name === form.platform) || {
    sell_fee_rate: 0,
    withdraw_fee_rate: 0,
    withdraw_min_fee: 0,
  }
);

const preview = computed(() => {
  const quantity = Number(form.quantity || 0);
  const price = Number(form.unit_price || 0);
  const gross = quantity > 0 && price > 0 ? quantity * price : 0;
  if (form.side === 'BUY') {
    return { gross, sellFee: 0, withdrawFee: 0, net: gross };
  }
  const sellFee = gross * Number(feeConfig.value.sell_fee_rate || 0);
  const afterTradeFee = gross - sellFee;
  const withdrawFee = Math.max(
    afterTradeFee * Number(feeConfig.value.withdraw_fee_rate || 0),
    Number(feeConfig.value.withdraw_min_fee || 0)
  );
  return { gross, sellFee, withdrawFee, net: afterTradeFee - withdrawFee };
});

const sellQuantityError = computed(() =>
  form.side === 'SELL' && Number(form.quantity || 0) > currentRemainingQuantity.value
);

const canSubmit = computed(() =>
  user.value?.email &&
  form.market_hash_name &&
  Number(form.quantity) > 0 &&
  Number(form.unit_price) > 0 &&
  !sellQuantityError.value
);

const fmtMoney = (value) => Number(value || 0).toLocaleString('zh-CN', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});
const fmtQty = (value) => Number(value || 0).toLocaleString('zh-CN', {
  maximumFractionDigits: 4,
});
const profitClass = (value) => Number(value || 0) >= 0 ? 'profit-positive' : 'profit-negative';
const platformName = (platform) =>
  platformFees.value.find((fee) => fee.platform_name === platform)?.display_name || platform;

async function refreshAll() {
  if (!user.value?.email) return;
  loading.value = true;
  error.value = '';
  const [positionsResult, feesResult] = await Promise.all([
    api.getTradeNotePositions(user.value.email),
    api.getPlatformFees(),
  ]);
  loading.value = false;
  if (feesResult.success) {
    platformFees.value = feesResult.data;
    if (
      platformFees.value.length &&
      !platformFees.value.some((fee) => fee.platform_name === form.platform)
    ) {
      form.platform = platformFees.value[0].platform_name;
    }
  }
  if (positionsResult.success) {
    positions.value = positionsResult.data;
    const selectedRecord = positions.value.find(
      (position) => position.market_hash_name === selectedMarket.value
    );
    if (!selectedMarket.value && openPositions.value.length) {
      await selectPosition(openPositions.value[0]);
    } else if (!selectedMarket.value && closedPositions.value.length) {
      await selectPosition(closedPositions.value[0]);
    } else if (selectedRecord) {
      await loadEntries(selectedMarket.value);
    } else if (selectedMarket.value) {
      selectedMarket.value = null;
      entries.value = [];
      if (openPositions.value.length) {
        await selectPosition(openPositions.value[0]);
      } else if (closedPositions.value.length) {
        await selectPosition(closedPositions.value[0]);
      }
    }
  } else {
    error.value = positionsResult.error || '读取仓位失败';
  }
}

async function loadEntries(marketHashName) {
  if (!user.value?.email || !marketHashName) return;
  const result = await api.getTradeNoteEntries(user.value.email, marketHashName);
  entries.value = result.success ? result.data : [];
}

async function selectPosition(position) {
  selectedMarket.value = position.market_hash_name;
  form.market_hash_name = position.market_hash_name;
  form.item_name = position.item_name || position.market_hash_name;
  await loadEntries(position.market_hash_name);
}

async function pickItem(item) {
  form.market_hash_name = item.market_hash_name;
  form.item_name = item.name || item.market_hash_name;
  selectedMarket.value = item.market_hash_name;
  searchResults.value = [];
  const existing = positions.value.find((position) => position.market_hash_name === item.market_hash_name);
  if (existing) {
    await selectPosition(existing);
  } else {
    entries.value = [];
  }
}

function scheduleSearch() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(searchNow, 350);
}

async function searchNow() {
  const query = searchQuery.value.trim();
  if (!query) {
    searchResults.value = [];
    return;
  }
  searching.value = true;
  const result = await api.searchItems(query, 8);
  searching.value = false;
  searchResults.value = result.success ? result.data || [] : [];
}

async function submitEntry() {
  if (!canSubmit.value) return;
  saving.value = true;
  error.value = '';
  const result = await api.addTradeNoteEntry({
    email: user.value.email,
    market_hash_name: form.market_hash_name,
    item_name: form.item_name,
    side: form.side,
    platform: form.platform,
    trade_date: form.trade_date,
    quantity: Number(form.quantity),
    unit_price: Number(form.unit_price),
    note: form.note,
  });
  saving.value = false;
  if (!result.success) {
    error.value = result.error || '保存失败';
    return;
  }
  const market = form.market_hash_name;
  form.quantity = 1;
  form.unit_price = null;
  form.note = '';
  await refreshAll();
  const record = positions.value.find((position) => position.market_hash_name === market);
  if (record) {
    await selectPosition(record);
  } else if (!positions.value.length) {
    selectedMarket.value = null;
    entries.value = [];
  }
}

async function deleteEntry(entry) {
  if (!user.value?.email || !confirm('删除这条流水？')) return;
  const result = await api.deleteTradeNoteEntry(user.value.email, entry.id);
  if (result.success) {
    await refreshAll();
  } else {
    error.value = result.error || '删除失败';
  }
}

onMounted(refreshAll);
</script>

<style scoped>
.trade-notes-page {
  min-height: 100vh;
  padding: 20px;
  color: var(--primary-green);
  font-family: 'Share Tech Mono', 'Source Code Pro', monospace;
}
.tn-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(0, 255, 65, 0.16);
}
.tn-title { font-size: 22px; font-weight: 700; }
.tn-sub { font-size: 11px; color: rgba(0, 255, 65, 0.45); margin-top: 4px; }
.summary-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}
.summary-cell, .panel {
  background: rgba(0, 0, 0, 0.52);
  border: 1px solid rgba(0, 255, 65, 0.14);
  border-radius: 8px;
}
.summary-cell {
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.summary-cell span, label span {
  font-size: 11px;
  color: rgba(0, 255, 65, 0.45);
}
.summary-cell strong { font-size: 18px; }
.tn-grid {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 14px;
}
.panel { overflow: hidden; }
.panel-hd {
  min-height: 38px;
  padding: 10px 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid rgba(0, 255, 65, 0.08);
  background: rgba(0, 255, 65, 0.025);
  font-size: 13px;
  font-weight: 700;
}
.pc-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--primary-green);
  box-shadow: 0 0 6px var(--primary-green);
}
.count-pill {
  margin-left: auto;
  padding: 1px 7px;
  border: 1px solid rgba(0, 255, 65, 0.25);
  border-radius: 4px;
  font-size: 10px;
}
.positions-panel { max-height: calc(100vh - 150px); overflow-y: auto; }
.position-row, .result-row {
  width: 100%;
  border: 0;
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
  font-family: inherit;
}
.position-row {
  padding: 11px 14px;
  border-bottom: 1px solid rgba(0, 255, 65, 0.06);
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.position-section-title {
  padding: 9px 14px;
  border-top: 1px solid rgba(0, 255, 65, 0.1);
  border-bottom: 1px solid rgba(0, 255, 65, 0.06);
  display: flex;
  justify-content: space-between;
  color: rgba(0, 255, 65, 0.48);
  font-size: 11px;
  background: rgba(0, 255, 65, 0.025);
}
.position-row.closed {
  color: rgba(0, 255, 65, 0.72);
}
.position-row:hover, .position-row.selected { background: rgba(0, 255, 65, 0.07); }
.position-row.selected { border-left: 2px solid var(--primary-green); }
.pr-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 13px;
}
.pr-meta {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: rgba(0, 255, 65, 0.42);
}
.workspace {
  display: grid;
  gap: 14px;
}
.search-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 90px;
  gap: 8px;
  padding: 12px 14px;
}
.field {
  width: 100%;
  min-height: 34px;
  border-radius: 5px;
  border: 1px solid rgba(0, 255, 65, 0.16);
  background: rgba(0, 0, 0, 0.45);
  color: var(--primary-green);
  padding: 7px 9px;
  font-family: inherit;
}
.field:focus { outline: 1px solid rgba(0, 255, 65, 0.35); }
.action-btn, .ghost-btn, .submit-btn, .mini-btn {
  border-radius: 5px;
  border: 1px solid rgba(0, 255, 65, 0.25);
  background: rgba(0, 255, 65, 0.08);
  color: var(--primary-green);
  font-family: inherit;
  cursor: pointer;
}
.action-btn, .ghost-btn { min-height: 34px; padding: 0 12px; }
.result-list { border-top: 1px solid rgba(0, 255, 65, 0.08); }
.result-row {
  padding: 9px 14px;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  border-bottom: 1px solid rgba(0, 255, 65, 0.05);
}
.result-row small { color: rgba(0, 255, 65, 0.35); }
.selected-item {
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 3px;
  border-bottom: 1px solid rgba(0, 255, 65, 0.06);
}
.selected-item small { color: rgba(0, 255, 65, 0.38); }
.form-grid {
  padding: 12px 14px;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
  align-items: end;
}
.segmented {
  display: grid;
  grid-template-columns: 1fr 1fr;
  border: 1px solid rgba(0, 255, 65, 0.18);
  border-radius: 5px;
  overflow: hidden;
}
.segmented button {
  min-height: 34px;
  border: 0;
  background: transparent;
  color: rgba(0, 255, 65, 0.55);
  font-family: inherit;
  cursor: pointer;
}
.segmented button.active {
  color: #001b0a;
  background: var(--primary-green);
}
label { display: flex; flex-direction: column; gap: 5px; }
.note-field { grid-column: span 2; }
.calc-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  padding: 0 14px 12px;
  font-size: 12px;
  color: rgba(0, 255, 65, 0.55);
}
.submit-btn {
  margin: 0 14px 14px;
  min-height: 38px;
  width: calc(100% - 28px);
  font-weight: 700;
}
.position-summary {
  padding: 12px 14px;
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 10px;
  border-bottom: 1px solid rgba(0, 255, 65, 0.08);
}
.position-summary div {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.position-summary span {
  color: rgba(0, 255, 65, 0.42);
  font-size: 10px;
}
.entry-table { overflow-x: auto; }
.entry-head, .entry-row {
  min-width: 820px;
  display: grid;
  grid-template-columns: 100px 60px 100px 90px 100px 120px 120px 50px;
  gap: 8px;
  align-items: center;
  padding: 8px 14px;
  font-size: 12px;
}
.entry-head {
  color: rgba(0, 255, 65, 0.42);
  border-bottom: 1px solid rgba(0, 255, 65, 0.08);
}
.entry-row { border-bottom: 1px solid rgba(0, 255, 65, 0.04); }
.mini-btn { min-height: 24px; }
.empty-line, .error-line, .hint-line {
  padding: 22px 14px;
  color: rgba(0, 255, 65, 0.38);
  font-size: 13px;
}
.error-line { color: #ff6666; padding-top: 0; }
.hint-line { color: #ffd166; padding-top: 0; }
.profit-positive { color: #00ff41 !important; }
.profit-negative { color: #ff4d4d !important; }
button:disabled { opacity: 0.45; cursor: not-allowed; }
@media (max-width: 1100px) {
  .summary-strip { grid-template-columns: repeat(2, 1fr); }
  .tn-grid { grid-template-columns: 1fr; }
  .form-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .position-summary { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 620px) {
  .summary-strip, .search-row, .form-grid { grid-template-columns: 1fr; }
  .note-field { grid-column: span 1; }
}
</style>
