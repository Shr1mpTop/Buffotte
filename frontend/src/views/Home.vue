<template>
  <BootAnimation v-if="showBoot" @complete="onBootDone" />
  <div v-show="!showBoot" ref="root" class="hq">

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
        SYSTEME ACTIF &nbsp;·&nbsp; {{ user?.username || 'ANONYMOUS' }}
        &nbsp;·&nbsp; {{ sessionTime }}
      </div>
    </header>

    <!-- STATS STRIP -->
    <div ref="stripEl" class="strip">
      <div class="st-cell">
        <span class="st-lbl">CPU</span>
        <div class="st-bar"><div ref="cpuBar" class="st-fill" style="width:0"></div></div>
        <span class="st-val">82%</span>
      </div>
      <div class="st-cell">
        <span class="st-lbl">MEM</span>
        <div class="st-bar"><div ref="memBar" class="st-fill" style="width:0"></div></div>
        <span class="st-val">58%</span>
      </div>
      <div class="st-cell">
        <span class="st-lbl">NET</span>
        <div class="st-bar accent"><div ref="netBar" class="st-fill accent" style="width:0"></div></div>
        <span class="st-val" style="color:#00ff41">SECURE</span>
      </div>
      <div class="st-cell uptime">
        <span class="st-lbl">UPTIME</span>
        <span class="st-val mono">{{ sessionTime }}</span>
      </div>
    </div>

    <!-- CARDS -->
    <div ref="gridEl" class="grid">

      <!-- 1: System status -->
      <div ref="c0" class="card">
        <div class="c-glow"></div>
        <div class="c-hd"><span class="c-dot"></span>系统状态<span class="badge ok">ONLINE</span></div>
        <div class="c-bd">
          <div class="kv"><span class="kv-k">▸ 状态</span><span class="kv-v ok">● ACTIVE</span></div>
          <div class="kv"><span class="kv-k">▸ 会话</span><span class="kv-v">{{ sessionTime }}</span></div>
          <div class="prog-group">
            <div class="pg-row"><span>系统负载</span><span ref="ldNum" class="pg-pct">0%</span></div>
            <div class="pg-track"><div ref="ldBar" class="pg-fill"></div></div>
          </div>
          <div class="prog-group">
            <div class="pg-row"><span>安全指数</span><span ref="scNum" class="pg-pct ok">0%</span></div>
            <div class="pg-track"><div ref="scBar" class="pg-fill ok"></div></div>
          </div>
        </div>
      </div>

      <!-- 2: User profile -->
      <div ref="c1" class="card">
        <div class="c-glow"></div>
        <div class="c-hd"><span class="c-dot"></span>用户档案</div>
        <div class="c-bd profile-bd">
          <div class="avatar-wrap">
            <div class="avatar">{{ (user?.username || 'A')[0].toUpperCase() }}</div>
          </div>
          <div class="pinfo">
            <div class="pi" v-for="r in pRows" :key="r.k">
              <span class="pi-k">{{ r.k }}</span>
              <span class="pi-v">{{ r.v }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 3: Quick actions -->
      <div ref="c2" class="card">
        <div class="c-glow"></div>
        <div class="c-hd"><span class="c-dot"></span>快速操作</div>
        <div class="c-bd">
          <router-link v-for="a in ACTIONS" :key="a.to" :to="a.to" class="act-btn">
            <span class="ab-ic">{{ a.ic }}</span>
            <span class="ab-txt">{{ a.label }}</span>
            <span class="ab-arr">→</span>
          </router-link>
        </div>
      </div>

      <!-- 4: Data panel -->
      <div ref="c3" class="card">
        <div class="c-glow"></div>
        <div class="c-hd"><span class="c-dot"></span>数据面板</div>
        <div class="c-bd data-bd">
          <template v-if="userDetails">
            <div class="ring-wrap">
              <svg class="ring-svg" viewBox="0 0 80 80" width="90" height="90">
                <circle cx="40" cy="40" r="32" class="ring-bg" />
                <circle cx="40" cy="40" r="32" class="ring-track"
                  :style="{ strokeDashoffset: ringOffset }" />
              </svg>
              <div class="ring-center">
                <span class="ring-n">{{ userDetails.tracked_count }}</span>
                <span class="ring-d">/ {{ userDetails.track_permit }}</span>
              </div>
            </div>
            <div class="ring-lbl">追踪饰品</div>
            <div class="lv-row">
              <span class="lv-badge">LV.{{ userDetails.level }}</span>
              <span class="lv-name">{{ userDetails.level_name }}</span>
            </div>
          </template>
          <div v-else-if="loadingDetails" class="ph">扫描中<span class="dots">...</span></div>
          <div v-else class="ph">[等待数据]</div>
        </div>
      </div>
    </div>

    <!-- TICKER -->
    <div ref="tickerEl" class="ticker">
      <div ref="tickInner" class="tick-inner">
        BUFFOTTE v2.0 &nbsp;•&nbsp; CS2 SKIN INTELLIGENCE &nbsp;•&nbsp; POWERED BY AI &nbsp;•&nbsp; DATA SECURED &nbsp;•&nbsp; ALL SYSTEMS NOMINAL &nbsp;•&nbsp;&emsp;
        BUFFOTTE v2.0 &nbsp;•&nbsp; CS2 SKIN INTELLIGENCE &nbsp;•&nbsp; POWERED BY AI &nbsp;•&nbsp; DATA SECURED &nbsp;•&nbsp; ALL SYSTEMS NOMINAL &nbsp;•&nbsp;&emsp;
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import gsap from 'gsap'
import BootAnimation from '../components/BootAnimation.vue'
import { client } from '../services/api'

// DOM refs
const root        = ref(null)
const matrixCanvas = ref(null)
const headerEl    = ref(null)
const typedEl     = ref(null)
const stripEl     = ref(null)
const gridEl      = ref(null)
const c0 = ref(null); const c1 = ref(null)
const c2 = ref(null); const c3 = ref(null)
const ldBar = ref(null); const ldNum = ref(null)
const scBar = ref(null); const scNum = ref(null)
const cpuBar = ref(null); const memBar = ref(null); const netBar = ref(null)
const tickerEl  = ref(null)
const tickInner = ref(null)

// state
const user           = ref(null)
const sessionTime    = ref('00:00:00')
const showBoot       = ref(false)
const userDetails    = ref(null)
const loadingDetails = ref(false)

const CIRC = 2 * Math.PI * 32
const ACTIONS = [
  { to: '/kline',    ic: 'K', label: 'K线数据' },
  { to: '/news',     ic: 'N', label: '最新资讯' },
  { to: '/tracking', ic: 'T', label: '管理追踪' },
  { to: '/skins',    ic: 'S', label: '热点皮肤' },
]

const ringOffset = computed(() => {
  if (!userDetails.value) return CIRC
  const pct = Math.min(userDetails.value.tracked_count / Math.max(userDetails.value.track_permit, 1), 1)
  return CIRC * (1 - pct)
})

const pRows = computed(() => {
  const rows = [
    { k: '用户名', v: user.value?.username || '未设置' },
    { k: '邮箱',   v: user.value?.email    || '未设置' },
    { k: '注册',   v: formatReg(user.value?.created_at) },
  ]
  if (userDetails.value) {
    rows.push({ k: '等级', v: `Lv.${userDetails.value.level} · ${userDetails.value.level_name}` })
    rows.push({ k: '可追踪', v: `${userDetails.value.track_permit} 件` })
  }
  return rows
})

const formatReg = ts => {
  if (!ts) return '未设置'
  return `注册 ${Math.ceil((Date.now() - new Date(ts)) / 86400000)} 天`
}

let _startTime = Date.now()
let _timer = null
const _tick = () => {
  const s = Math.floor((Date.now() - _startTime) / 1000)
  sessionTime.value = [
    String(Math.floor(s / 3600)).padStart(2, '0'),
    String(Math.floor((s % 3600) / 60)).padStart(2, '0'),
    String(s % 60).padStart(2, '0'),
  ].join(':')
}

// Matrix rain
let _raf = null
let _matrixCleanup = null
const initMatrix = () => {
  const c = matrixCanvas.value
  if (!c) return
  const ctx = c.getContext('2d')
  const FS = 13
  const JP = 'ｦｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈ0123456789ABCDEF@#$%'
  let cols, drops
  const resize = () => {
    c.width  = window.innerWidth
    c.height = window.innerHeight
    cols  = Math.ceil(c.width / FS)
    drops = Array.from({ length: cols }, () => -(Math.random() * (c.height / FS)))
  }
  resize()
  window.addEventListener('resize', resize)
  const draw = () => {
    ctx.fillStyle = 'rgba(0,0,0,0.05)'
    ctx.fillRect(0, 0, c.width, c.height)
    ctx.font = `${FS}px monospace`
    for (let i = 0; i < cols; i++) {
      const ch = JP[Math.floor(Math.random() * JP.length)]
      const y  = drops[i] * FS
      ctx.fillStyle = drops[i] < 2 ? 'rgba(200,255,200,0.8)' : `rgba(0,255,65,${Math.random() * 0.18 + 0.03})`
      ctx.fillText(ch, i * FS, y)
      if (y > c.height && Math.random() > 0.975) drops[i] = 0
      drops[i] += 0.35
    }
    _raf = requestAnimationFrame(draw)
  }
  draw()
  _matrixCleanup = () => {
    window.removeEventListener('resize', resize)
    if (_raf) cancelAnimationFrame(_raf)
  }
}

// Typewriter
const typewriter = async (el, text, msBase = 42) => {
  el.textContent = ''
  for (const ch of text) {
    el.textContent += ch
    await new Promise(r => setTimeout(r, msBase + Math.random() * 22))
  }
}

// Hacker scramble glitch
const scramble = el => {
  if (!el) return
  const orig = el.textContent
  const POOL = '!<>-_\\/[]{}=+^?#$ABCDEFabcdef0123456789'
  let i = 0
  const id = setInterval(() => {
    el.textContent = orig.split('').map((c, idx) =>
      idx < i ? orig[idx] : POOL[Math.floor(Math.random() * POOL.length)]
    ).join('')
    i += 1
    if (i > orig.length) clearInterval(id)
  }, 28)
}

// GSAP timeline
let _ctx = null
const initGSAP = () => {
  _ctx = gsap.context(() => {
    const tl = gsap.timeline({ delay: 0.05 })

    tl.fromTo(headerEl.value,
      { opacity: 0, y: -28 },
      { opacity: 1, y: 0, duration: 0.55, ease: 'power2.out' })

    tl.fromTo(stripEl.value,
      { opacity: 0, x: -24 },
      { opacity: 1, x: 0, duration: 0.4, ease: 'power2.out' },
      '-=0.2')

    tl.fromTo([c0.value, c1.value, c2.value, c3.value],
      { opacity: 0, y: 36, scale: 0.96 },
      { opacity: 1, y: 0, scale: 1, duration: 0.55, stagger: 0.1, ease: 'power3.out' },
      '-=0.1')

    tl.call(() => {
      gsap.to(ldBar.value, { width: '76%', duration: 1.3, ease: 'power2.out' })
      setTimeout(() => { if (ldNum.value) ldNum.value.textContent = '76%' }, 1300)
      gsap.to(scBar.value, { width: '99%', duration: 1.4, ease: 'power2.out', delay: 0.2 })
      setTimeout(() => { if (scNum.value) scNum.value.textContent = '99%' }, 1600)
      gsap.to(cpuBar.value, { width: '82%', duration: 1.1, ease: 'power2.out' })
      gsap.to(memBar.value, { width: '58%', duration: 1.1, ease: 'power2.out', delay: 0.1 })
      gsap.to(netBar.value, { width: '100%', duration: 0.8, ease: 'power2.out' })
    }, '-=0.2')

    tl.fromTo(tickerEl.value,
      { opacity: 0 },
      { opacity: 1, duration: 0.4 },
      '-=0.3')

    tl.call(() => {
      const el = tickInner.value
      if (!el) return
      const halfW = el.scrollWidth / 2
      gsap.to(el, { x: -halfW, duration: 28, ease: 'none', repeat: -1 })
    })

    gsap.to('.c-glow', {
      opacity: 0.85, duration: 2.2, yoyo: true, repeat: -1,
      stagger: { each: 0.5, from: 'random' }, ease: 'sine.inOut',
    })
  }, root.value)
}

const startAll = () => {
  initMatrix()
  initGSAP()
  setTimeout(async () => {
    if (!typedEl.value) return
    const cmd = `./dashboard.sh --user=${user.value?.username || 'guest'} --mode=live`
    await typewriter(typedEl.value, cmd, 42)
    const loop = () => {
      setTimeout(() => { scramble(typedEl.value); setTimeout(loop, 600) }, 5000 + Math.random() * 9000)
    }
    setTimeout(loop, 1500)
  }, 200)
}

const onBootDone = () => {
  showBoot.value = false
  nextTick(startAll)
}

onMounted(async () => {
  try { user.value = JSON.parse(localStorage.getItem('user')) } catch {}
  if (sessionStorage.getItem('firstLogin') === 'true') {
    showBoot.value = true
    sessionStorage.removeItem('firstLogin')
  }
  _timer = setInterval(_tick, 1000)
  if (!showBoot.value) startAll()

  if (user.value?.email) {
    loadingDetails.value = true
    try {
      const r = await client.get(`/user/details/${user.value.email}`)
      userDetails.value = r.data
    } catch { /* silent */ } finally {
      loadingDetails.value = false
    }
  }
})

onUnmounted(() => {
  if (_timer) clearInterval(_timer)
  if (_matrixCleanup) _matrixCleanup()
  if (_ctx) _ctx.revert()
})
</script>

<style scoped>
.hq {
  position: relative;
  width: 100%;
  max-width: 1200px;
  margin: 36px auto 0;
  padding: 0 24px 80px;
  z-index: 1;
}

/* Matrix canvas */
.matrix-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  opacity: 0.4;
}

/* Scanlines */
.scanlines {
  position: fixed;
  inset: 0;
  z-index: 9990;
  pointer-events: none;
  background: repeating-linear-gradient(
    0deg, transparent, transparent 2px,
    rgba(0,0,0,0.04) 2px, rgba(0,0,0,0.04) 4px
  );
  animation: scanmove 12s linear infinite;
}
@keyframes scanmove {
  from { background-position: 0 0; }
  to   { background-position: 0 100vh; }
}

/* Header */
.hdr {
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(0,255,65,0.18);
}
.hdr-prompt {
  font-size: 18px;
  font-weight: 700;
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  line-height: 1.7;
}
.p-usr  { color: #00e5ff; text-shadow: 0 0 8px rgba(0,229,255,0.5); }
.p-at   { color: rgba(0,255,65,0.6); }
.p-host { color: var(--primary-green); text-shadow: 0 0 8px rgba(0,255,65,0.5); }
.p-sep  { color: rgba(0,255,65,0.45); }
.p-cmd  { color: var(--primary-green); min-width: 2ch; }
.p-cur  { color: var(--primary-green); animation: blink 1s step-end infinite; margin-left: 1px; }
@keyframes blink { 50% { opacity: 0; } }

.hdr-meta {
  margin-top: 6px;
  font-size: 12px;
  color: rgba(0,255,65,0.5);
  letter-spacing: 1.2px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.hm-dot {
  display: inline-block;
  width: 7px; height: 7px;
  border-radius: 50%;
  background: #00ff41;
  box-shadow: 0 0 8px #00ff41;
  animation: pdot 2s ease-in-out infinite;
}
@keyframes pdot {
  0%,100% { box-shadow: 0 0 4px #00ff41; }
  50%     { box-shadow: 0 0 14px #00ff41, 0 0 28px rgba(0,255,65,0.35); }
}

/* Stats strip */
.strip {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  padding: 10px 14px;
  background: rgba(0,20,0,0.55);
  border: 1px solid rgba(0,255,65,0.1);
  border-radius: 6px;
  backdrop-filter: blur(8px);
  flex-wrap: wrap;
}
.st-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 110px;
}
.st-lbl { font-size: 10px; color: rgba(0,255,65,0.48); letter-spacing: 1.5px; width: 32px; flex-shrink: 0; }
.st-bar { flex: 1; height: 4px; background: rgba(0,255,65,0.08); border-radius: 2px; overflow: hidden; }
.st-fill { height: 100%; background: linear-gradient(90deg,#00cc33,#00ff41); border-radius: 2px; box-shadow: 0 0 6px rgba(0,255,65,0.4); }
.st-fill.accent { background: linear-gradient(90deg,#00e5ff,#00ff41); }
.st-bar.accent  { background: rgba(0,229,255,0.08); }
.st-val { font-size: 11px; color: var(--primary-green); width: 42px; text-align: right; flex-shrink: 0; }
.uptime .st-val { width: auto; }
.mono { font-variant-numeric: tabular-nums; }

/* Grid */
.grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}
@media (max-width: 700px) {
  .grid { grid-template-columns: 1fr; }
  .uptime { display: none; }
}

/* Card */
.card {
  position: relative;
  background: rgba(4,14,4,0.88);
  border: 1px solid rgba(0,255,65,0.15);
  border-radius: 8px;
  overflow: hidden;
  backdrop-filter: blur(14px);
  transition: border-color 0.3s, transform 0.25s, box-shadow 0.3s;
}
.card:hover {
  border-color: rgba(0,255,65,0.38);
  transform: translateY(-4px);
  box-shadow: 0 8px 32px rgba(0,255,65,0.1);
}
.card::before, .card::after {
  content: '';
  position: absolute;
  width: 10px; height: 10px;
  border-color: rgba(0,255,65,0.45);
  border-style: solid;
}
.card::before { top: 0; left: 0; border-width: 2px 0 0 2px; }
.card::after  { bottom: 0; right: 0; border-width: 0 2px 2px 0; }

.c-glow {
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at top left, rgba(0,255,65,0.07) 0%, transparent 66%);
  opacity: 0.3;
  pointer-events: none;
}

.c-hd {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  font-size: 13px;
  font-weight: 600;
  color: var(--primary-green);
  border-bottom: 1px solid rgba(0,255,65,0.08);
  background: rgba(0,255,65,0.025);
  letter-spacing: 0.5px;
}
.c-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--primary-green);
  box-shadow: 0 0 6px var(--primary-green);
  flex-shrink: 0;
}
.badge {
  margin-left: auto;
  font-size: 10px;
  padding: 2px 7px;
  border-radius: 3px;
  letter-spacing: 1px;
  border: 1px solid;
}
.badge.ok { color: #00ff41; border-color: rgba(0,255,65,0.35); background: rgba(0,255,65,0.07); }
.c-bd { padding: 16px; }

/* KV rows */
.kv { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 8px; }
.kv-k { color: rgba(0,255,65,0.55); }
.kv-v { color: var(--primary-green); font-weight: 500; }
.kv-v.ok { color: #00ff8b; text-shadow: 0 0 8px rgba(0,255,139,0.45); }
.ok { color: #00ff41 !important; }

/* Progress bars */
.prog-group { margin-top: 10px; }
.pg-row { display: flex; justify-content: space-between; font-size: 11px; color: rgba(0,255,65,0.55); margin-bottom: 4px; }
.pg-pct { color: var(--primary-green); }
.pg-track { height: 5px; background: rgba(0,255,65,0.07); border-radius: 3px; overflow: hidden; margin-bottom: 2px; }
.pg-fill { height: 100%; background: linear-gradient(90deg,#00cc33,#00ff88); border-radius: 3px; box-shadow: 0 0 8px rgba(0,255,65,0.35); width: 0; }
.pg-fill.ok { background: linear-gradient(90deg,#00e5ff,#00ff41); box-shadow: 0 0 8px rgba(0,229,255,0.35); }

/* Profile card */
.profile-bd { display: flex; gap: 14px; align-items: flex-start; }
.avatar-wrap { flex-shrink: 0; }
.avatar {
  width: 52px; height: 52px;
  background: rgba(0,255,65,0.07);
  border: 2px solid rgba(0,255,65,0.38);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; font-weight: 700;
  color: var(--primary-green);
  text-shadow: 0 0 12px rgba(0,255,65,0.5);
  box-shadow: 0 0 18px rgba(0,255,65,0.12), inset 0 0 12px rgba(0,255,65,0.04);
  position: relative;
}
.avatar::after {
  content: '';
  position: absolute;
  inset: -6px;
  border-radius: 50%;
  border: 1px solid rgba(0,255,65,0.15);
  animation: spin-ring 8s linear infinite;
}
@keyframes spin-ring { to { transform: rotate(360deg); } }
.pinfo { flex: 1; min-width: 0; }
.pi { display: flex; gap: 6px; font-size: 12px; margin-bottom: 6px; line-height: 1.4; }
.pi-k { color: rgba(0,255,65,0.48); width: 46px; flex-shrink: 0; }
.pi-v { color: var(--primary-green); font-weight: 500; word-break: break-all; }

/* Action buttons */
.act-btn {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 10px;
  border: 1px solid rgba(0,255,65,0.1);
  border-radius: 5px;
  text-decoration: none;
  color: var(--primary-green);
  font-size: 13px;
  margin-bottom: 8px;
  background: rgba(0,255,65,0.02);
  transition: background 0.2s, border-color 0.2s, transform 0.2s;
}
.act-btn:last-child { margin-bottom: 0; }
.act-btn:hover { background: rgba(0,255,65,0.07); border-color: rgba(0,255,65,0.32); transform: translateX(4px); }
.ab-ic {
  display: flex; align-items: center; justify-content: center;
  width: 22px; height: 22px;
  border: 1px solid rgba(0,255,65,0.38);
  border-radius: 4px;
  font-size: 11px; font-weight: 700;
  color: var(--primary-green);
  background: rgba(0,255,65,0.05);
  flex-shrink: 0;
}
.ab-txt { flex: 1; }
.ab-arr { color: rgba(0,255,65,0.38); transition: transform 0.2s, color 0.2s; }
.act-btn:hover .ab-arr { transform: translateX(3px); color: var(--primary-green); }

/* Data panel */
.data-bd { display: flex; flex-direction: column; align-items: center; gap: 10px; }
.ring-wrap { position: relative; display: inline-flex; align-items: center; justify-content: center; }
.ring-svg { display: block; overflow: visible; }
.ring-bg   { fill: none; stroke: rgba(0,255,65,0.1); stroke-width: 4; }
.ring-track {
  fill: none; stroke: #00ff41; stroke-width: 4; stroke-linecap: round;
  stroke-dasharray: 201.06;
  transform-origin: 40px 40px;
  transform: rotate(-90deg);
  filter: drop-shadow(0 0 6px rgba(0,255,65,0.55));
  transition: stroke-dashoffset 1s ease;
}
.ring-center { position: absolute; display: flex; flex-direction: column; align-items: center; line-height: 1.2; }
.ring-n { font-size: 20px; font-weight: 700; color: var(--primary-green); text-shadow: 0 0 10px rgba(0,255,65,0.45); }
.ring-d { font-size: 11px; color: rgba(0,255,65,0.48); }
.ring-lbl { font-size: 12px; color: rgba(0,255,65,0.55); letter-spacing: 1px; }
.lv-row { display: flex; align-items: center; gap: 10px; }
.lv-badge {
  padding: 3px 10px;
  background: rgba(0,255,65,0.08);
  border: 1px solid rgba(0,255,65,0.32);
  border-radius: 4px;
  font-size: 12px; font-weight: 700;
  color: var(--primary-green);
  text-shadow: 0 0 8px rgba(0,255,65,0.35);
  letter-spacing: 1px;
}
.lv-name { font-size: 13px; color: rgba(0,255,65,0.65); }
.ph { color: rgba(0,255,65,0.38); font-size: 13px; text-align: center; padding: 20px 0; }
.dots { animation: dotanim 1.2s step-end infinite; }
@keyframes dotanim { 0%,100%{opacity:1}33%{opacity:0}66%{opacity:.5} }

/* Ticker */
.ticker {
  margin-top: 22px;
  overflow: hidden;
  border-top: 1px solid rgba(0,255,65,0.1);
  border-bottom: 1px solid rgba(0,255,65,0.1);
  background: rgba(0,255,65,0.015);
  padding: 7px 0;
  white-space: nowrap;
}
.tick-inner {
  display: inline-block;
  font-size: 11px;
  color: rgba(0,255,65,0.42);
  letter-spacing: 1.5px;
  white-space: nowrap;
}
</style>
