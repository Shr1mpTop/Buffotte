<template>
  <div ref="sidebarEl" class="sidebar" :class="{ collapsed }">
    <!-- Matrix rain canvas -->
    <canvas ref="matrixCanvas" class="matrix-bg" aria-hidden="true"></canvas>
    <!-- Scanlines overlay -->
    <div class="scanlines" aria-hidden="true"></div>

    <!-- Toggle button -->
    <button class="toggle-btn" @click="collapsed = !collapsed" :title="collapsed ? '展开' : '折叠'">
      <span class="toggle-icon" :class="{ rotated: collapsed }">◁</span>
    </button>

    <!-- Header -->
    <div class="sidebar-header">
      <div class="logo-row">
        <span class="pc-dot"></span>
        <span class="logo">BUFFOTTE</span>
      </div>
      <div class="subtitle" v-if="!collapsed">root@console:~# <span class="p-cur">█</span></div>
    </div>

    <!-- Navigation -->
    <nav class="sidebar-nav">
      <router-link
        v-for="(item, idx) in navItems"
        :key="item.to"
        :to="item.to"
        class="nav-item"
        :class="{ active: $route.path === item.to }"
        :title="collapsed ? item.label : ''"
        :ref="(el) => { if (el) navRefs[idx] = el }"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span class="nav-text" v-if="!collapsed">{{ item.label }}</span>
      </router-link>
    </nav>

    <!-- Footer -->
    <div class="sidebar-footer">
      <template v-if="!collapsed">
        <div class="user-info" v-if="user">
          <div class="ui-row"><span class="ui-k">▸</span><span class="ui-v">{{ user.username }}</span></div>
          <div class="ui-row"><span class="ui-k">●</span><span class="ui-v ui-dim">{{ sessionTime }}</span></div>
        </div>
      </template>
      <button class="logout-btn" @click="logout" :title="collapsed ? '登出' : ''">
        <span class="logout-icon">◁</span>
        <span class="nav-text" v-if="!collapsed">登出</span>
      </button>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, onUnmounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import gsap from 'gsap';

export default {
  name: 'Sidebar',
  emits: ['collapse-change'],
  setup(props, { emit }) {
    const router = useRouter();
    const route = useRoute();
    const sidebarEl = ref(null);
    const matrixCanvas = ref(null);
    const navRefs = reactive({});
    const collapsed = ref(false);
    const user = ref(JSON.parse(localStorage.getItem('user')));
    const sessionTime = ref('00:00:00');

    const navItems = [
      { to: '/dashboard', icon: '▸', label: '首页' },
      { to: '/kline',     icon: '◆', label: '市场' },
      { to: '/items',     icon: '◈', label: '饰品' },
      { to: '/news',      icon: '◎', label: '资讯' },
      { to: '/skins',     icon: '★', label: '热点' },
      { to: '/tracking',  icon: '◉', label: '追踪' },
    ];

    // --- Session timer ---
    let _startTime = Date.now();
    let _timer = null;
    const tick = () => {
      const s = Math.floor((Date.now() - _startTime) / 1000);
      sessionTime.value = [
        String(Math.floor(s / 3600)).padStart(2, '0'),
        String(Math.floor((s % 3600) / 60)).padStart(2, '0'),
        String(s % 60).padStart(2, '0'),
      ].join(':');
    };

    // --- Matrix rain (mini) ---
    let _raf = null;
    let _matrixCleanup = null;
    const initMatrix = () => {
      const c = matrixCanvas.value;
      if (!c) return;
      const ctx = c.getContext('2d');
      const FS = 11;
      const JP = 'ｦｱｲｳｴｵｶｷｸｹ01234567ABCDEF@#$%';
      let cols, drops;
      const resize = () => {
        c.width = 220;
        c.height = window.innerHeight;
        cols = Math.ceil(c.width / FS);
        drops = Array.from({ length: cols }, () => -(Math.random() * (c.height / FS)));
      };
      resize();
      window.addEventListener('resize', resize);
      const draw = () => {
        ctx.fillStyle = 'rgba(0,0,0,0.06)';
        ctx.fillRect(0, 0, c.width, c.height);
        ctx.font = `${FS}px monospace`;
        for (let i = 0; i < cols; i++) {
          const ch = JP[Math.floor(Math.random() * JP.length)];
          const y = drops[i] * FS;
          ctx.fillStyle = drops[i] < 2
            ? 'rgba(200,255,200,0.5)'
            : `rgba(0,255,65,${Math.random() * 0.1 + 0.02})`;
          ctx.fillText(ch, i * FS, y);
          if (y > c.height && Math.random() > 0.975) drops[i] = 0;
          drops[i] += 0.25;
        }
        _raf = requestAnimationFrame(draw);
      };
      draw();
      _matrixCleanup = () => {
        window.removeEventListener('resize', resize);
        if (_raf) cancelAnimationFrame(_raf);
      };
    };

    // --- GSAP entrance ---
    const initGSAP = () => {
      if (!sidebarEl.value) return;
      gsap.fromTo(sidebarEl.value,
        { opacity: 0, x: -40 },
        { opacity: 1, x: 0, duration: 0.5, ease: 'power2.out' }
      );
      const items = Object.values(navRefs);
      if (items.length) {
        gsap.fromTo(items,
          { opacity: 0, x: -16 },
          { opacity: 1, x: 0, duration: 0.35, stagger: 0.06, ease: 'power2.out', delay: 0.25 }
        );
      }
    };

    // --- Collapse sync ---
    watch(collapsed, (val) => {
      emit('collapse-change', val);
    });

    // --- Logout ---
    const logout = () => {
      localStorage.removeItem('user');
      router.push('/login');
    };

    onMounted(() => {
      initMatrix();
      initGSAP();
      _timer = setInterval(tick, 1000);
      tick();
    });

    onUnmounted(() => {
      if (_matrixCleanup) _matrixCleanup();
      if (_timer) clearInterval(_timer);
    });

    return {
      sidebarEl, matrixCanvas, navRefs, collapsed,
      user, sessionTime, navItems, logout,
    };
  },
};
</script>

<style scoped>
.sidebar {
  --sb-width: 220px;
  --sb-mini: 56px;
  width: var(--sb-width);
  height: 100vh;
  background: rgba(0, 0, 0, 0.92);
  border-right: 1px solid rgba(0, 255, 65, 0.15);
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 100;
  font-family: 'Share Tech Mono', 'Source Code Pro', monospace;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}
.sidebar.collapsed {
  width: var(--sb-mini);
}

/* Matrix canvas */
.matrix-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  opacity: 0.2;
}

/* Scanlines */
.scanlines {
  position: absolute;
  inset: 0;
  z-index: 1;
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

/* Toggle button */
.toggle-btn {
  position: absolute;
  top: 12px;
  right: 8px;
  z-index: 10;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 255, 65, 0.06);
  border: 1px solid rgba(0, 255, 65, 0.2);
  border-radius: 4px;
  color: rgba(0, 255, 65, 0.6);
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}
.toggle-btn:hover {
  background: rgba(0, 255, 65, 0.12);
  border-color: rgba(0, 255, 65, 0.4);
  color: var(--primary-green);
}
.toggle-icon {
  display: inline-block;
  transition: transform 0.3s;
}
.toggle-icon.rotated {
  transform: rotate(180deg);
}

/* Header */
.sidebar-header {
  position: relative;
  z-index: 2;
  padding: 28px 20px 18px;
  border-bottom: 1px solid rgba(0, 255, 65, 0.1);
}
.collapsed .sidebar-header {
  padding: 28px 8px 18px;
}
.logo-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.logo {
  color: var(--primary-green);
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 2px;
  text-shadow: 0 0 10px rgba(0, 255, 65, 0.5), 0 0 20px rgba(0, 255, 65, 0.2);
  white-space: nowrap;
  overflow: hidden;
  transition: opacity 0.3s;
}
.collapsed .logo {
  font-size: 11px;
  letter-spacing: 0;
  opacity: 0.8;
}
.subtitle {
  color: rgba(0, 255, 65, 0.4);
  font-size: 11px;
  margin-top: 6px;
  white-space: nowrap;
  overflow: hidden;
}
.p-cur {
  animation: blink 1s step-end infinite;
}
@keyframes blink { 50% { opacity: 0; } }

/* pc-dot (shared with other pages) */
.pc-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--primary-green);
  box-shadow: 0 0 6px var(--primary-green);
  flex-shrink: 0;
}

/* Navigation */
.sidebar-nav {
  position: relative;
  z-index: 2;
  flex: 1;
  padding: 12px 0;
  overflow-y: auto;
  overflow-x: hidden;
}
.sidebar-nav::-webkit-scrollbar { width: 3px; }
.sidebar-nav::-webkit-scrollbar-track { background: transparent; }
.sidebar-nav::-webkit-scrollbar-thumb { background: rgba(0, 255, 65, 0.2); border-radius: 2px; }

.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 20px;
  color: rgba(0, 255, 65, 0.5);
  text-decoration: none;
  transition: all 0.25s;
  border-left: 2px solid transparent;
  white-space: nowrap;
  overflow: hidden;
}
.collapsed .nav-item {
  padding: 11px 0;
  justify-content: center;
  gap: 0;
}

.nav-icon {
  font-size: 14px;
  width: 20px;
  text-align: center;
  flex-shrink: 0;
  transition: color 0.25s, text-shadow 0.25s;
}
.collapsed .nav-icon {
  width: auto;
  font-size: 16px;
}

.nav-text {
  font-size: 13px;
  transition: opacity 0.2s;
}

/* Hover */
.nav-item:hover {
  color: var(--primary-green);
  background: rgba(0, 255, 65, 0.05);
  border-left-color: rgba(0, 255, 65, 0.3);
}
.nav-item:hover .nav-icon { text-shadow: 0 0 8px rgba(0, 255, 65, 0.6); }

/* Active */
.nav-item.active {
  color: var(--primary-green);
  background: rgba(0, 255, 65, 0.08);
  border-left-color: var(--primary-green);
  font-weight: 600;
}
.nav-item.active .nav-icon {
  text-shadow: 0 0 12px rgba(0, 255, 65, 0.8);
}
.nav-item.active::after {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--primary-green);
  box-shadow: 0 0 10px var(--primary-green);
}

/* Footer */
.sidebar-footer {
  position: relative;
  z-index: 2;
  padding: 12px 16px;
  border-top: 1px solid rgba(0, 255, 65, 0.1);
}
.collapsed .sidebar-footer {
  padding: 12px 8px;
}

.user-info {
  padding: 8px 10px;
  margin-bottom: 8px;
  background: rgba(0, 255, 65, 0.03);
  border: 1px solid rgba(0, 255, 65, 0.08);
  border-radius: 4px;
}
.ui-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  line-height: 1.8;
}
.ui-k { color: rgba(0, 255, 65, 0.4); }
.ui-v { color: var(--primary-green); }
.ui-dim { color: rgba(0, 255, 65, 0.4); }

.logout-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 10px 14px;
  background: transparent;
  border: 1px solid rgba(255, 80, 80, 0.2);
  color: rgba(255, 80, 80, 0.6);
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.25s;
  font-family: 'Share Tech Mono', monospace;
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
}
.logout-btn:hover {
  background: rgba(255, 80, 80, 0.08);
  border-color: rgba(255, 80, 80, 0.5);
  color: #ff5050;
}
.logout-icon {
  font-size: 13px;
  flex-shrink: 0;
}

/* Responsive */
@media (max-width: 900px) {
  .sidebar { width: var(--sb-mini); }
  .sidebar .nav-text,
  .sidebar .subtitle,
  .sidebar .logo,
  .sidebar .user-info { display: none; }
  .sidebar .nav-item { padding: 11px 0; justify-content: center; gap: 0; }
  .sidebar .sidebar-header { padding: 28px 8px 18px; }
  .sidebar .sidebar-footer { padding: 12px 8px; }
  .sidebar .toggle-btn { display: none; }
}
</style>
