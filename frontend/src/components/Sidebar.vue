<template>
  <div class="sidebar">
    <div class="sidebar-header">
      <div class="logo">BUFFOTTE</div>
      <div class="subtitle">控制台</div>
    </div>
    <nav class="sidebar-nav">
      <router-link to="/dashboard" class="nav-item" active-class="active">
        <span class="icon">■</span>
        <span class="text">首页</span>
      </router-link>
      <router-link to="/kline" class="nav-item" active-class="active">
        <span class="icon">▤</span>
        <span class="text">市场</span>
      </router-link>
      <router-link to="/items" class="nav-item" active-class="active">
        <span class="icon">💎</span>
        <span class="text">饰品</span>
      </router-link>
      <router-link to="/news" class="nav-item" active-class="active">
        <span class="icon">📰</span>
        <span class="text">资讯</span>
      </router-link>
      <router-link to="/tracking" class="nav-item" active-class="active">
        <span class="icon">★</span>
        <span class="text">追踪</span>
      </router-link>
    </nav>
    <div class="sidebar-footer">
      <button class="logout-btn" @click="logout">
        <span class="icon">✕</span>
        <span class="text">登出</span>
      </button>
    </div>
  </div>
</template>

<script>
import { useRouter } from 'vue-router'

export default {
  name: 'Sidebar',
  setup() {
    const router = useRouter()
    const logout = () => {
      localStorage.removeItem('user')
      router.push('/login')
    }
    return { logout }
  }
}
</script>

<style scoped>
.sidebar {
  width: 220px;
  height: 100vh;
  background: rgba(0, 0, 0, 0.95);
  border-right: 1px solid rgba(0, 255, 127, 0.2);
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 100;
  animation: slideInLeft 0.4s ease;
}

@keyframes slideInLeft {
  from {
    transform: translateX(-220px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.sidebar-header {
  padding: 24px 20px;
  border-bottom: 1px solid rgba(0, 255, 127, 0.1);
}

.logo {
  color: var(--primary-green);
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 2px;
  text-shadow: 0 0 10px rgba(0, 255, 127, 0.5);
}

.subtitle {
  color: var(--secondary-green);
  font-size: 12px;
  margin-top: 4px;
  opacity: 0.7;
}

.sidebar-nav {
  flex: 1;
  padding: 20px 0;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 14px 20px;
  color: rgba(0, 255, 127, 0.6);
  text-decoration: none;
  transition: all 0.2s;
  border-left: 3px solid transparent;
  position: relative;
}

.nav-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 0;
  height: 0;
  background: var(--primary-green);
  transition: all 0.3s;
  opacity: 0;
}

.nav-item:hover::before {
  width: 3px;
  height: 100%;
  opacity: 0.5;
}

.nav-item:hover {
  background: rgba(0, 255, 127, 0.05);
  color: var(--primary-green);
  border-left-color: rgba(0, 255, 127, 0.3);
}

.nav-item.active {
  background: rgba(0, 255, 127, 0.1);
  color: var(--primary-green);
  border-left-color: var(--primary-green);
  font-weight: 600;
}

.nav-item .icon {
  margin-right: 12px;
  font-size: 16px;
  width: 20px;
  text-align: center;
}

.nav-item .text {
  font-size: 14px;
}

.sidebar-footer {
  padding: 20px;
  border-top: 1px solid rgba(0, 255, 127, 0.1);
}

.logout-btn {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 12px 16px;
  background: transparent;
  border: 1px solid rgba(255, 107, 107, 0.3);
  color: rgba(255, 107, 107, 0.8);
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
  font-family: 'Source Code Pro', monospace;
}

.logout-btn:hover {
  background: rgba(255, 107, 107, 0.1);
  border-color: rgba(255, 107, 107, 0.6);
  color: #ff6b6b;
}

.logout-btn .icon {
  margin-right: 8px;
}
</style>
