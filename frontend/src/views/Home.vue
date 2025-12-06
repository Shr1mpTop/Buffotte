<template>
  <BootAnimation v-if="showBoot" @complete="showBoot = false" />
  <div v-show="!showBoot" class="dashboard">
    <div class="dashboard-header">
      <h1 class="title">$ ./dashboard.sh</h1>
      <div class="user-info">
        <span class="label">USER:</span>
        <span class="value">{{ user?.username || 'Anonymous' }}</span>
      </div>
    </div>
    <div class="dashboard-grid">
      <div class="card">
        <div class="card-header">系统状态</div>
        <div class="card-body">
          <div class="stat-line">
            <span class="stat-label">▸ 在线状态:</span>
            <span class="stat-value online">● ONLINE</span>
          </div>
          <div class="stat-line">
            <span class="stat-label">▸ 会话时间:</span>
            <span class="stat-value">{{ sessionTime }}</span>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="card-header">快速操作</div>
        <div class="card-body">
          <router-link to="/profile" class="action-link">→ 查看档案</router-link>
          <router-link to="/kline" class="action-link">→ K线数据</router-link>
        </div>
      </div>
      <div class="card placeholder">
        <div class="card-header">数据面板</div>
        <div class="card-body">
          <div class="placeholder-text">[占位区域]</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import BootAnimation from '../components/BootAnimation.vue'
import { ref, onMounted, onUnmounted } from 'vue'

export default {
  name: 'Dashboard',
  components: { BootAnimation },
  setup() {
    const user = ref(null)
    const sessionTime = ref('00:00:00')
    const showBoot = ref(false)
    let startTime = Date.now()
    let timer = null

    const updateSessionTime = () => {
      const elapsed = Math.floor((Date.now() - startTime) / 1000)
      const h = Math.floor(elapsed / 3600).toString().padStart(2, '0')
      const m = Math.floor((elapsed % 3600) / 60).toString().padStart(2, '0')
      const s = (elapsed % 60).toString().padStart(2, '0')
      sessionTime.value = `${h}:${m}:${s}`
    }

    onMounted(() => {
      try {
        user.value = JSON.parse(localStorage.getItem('user'))
      } catch (e) {}
      
      // 检查是否是首次登录进入
      const isFirstLogin = sessionStorage.getItem('firstLogin')
      if (isFirstLogin === 'true') {
        showBoot.value = true
        sessionStorage.removeItem('firstLogin')
      }
      
      timer = setInterval(updateSessionTime, 1000)
    })

    onUnmounted(() => {
      if (timer) clearInterval(timer)
    })

    return { user, sessionTime, showBoot }
  }
}
</script>

<style scoped>
.dashboard {
  width: 100%;
  max-width: 1200px;
  padding: 24px;
  margin: 40px 0 0 0;
  animation: fadeIn 0.4s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.dashboard-header {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(0, 255, 127, 0.2);
}

.title {
  color: var(--primary-green);
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 12px 0;
  text-shadow: 0 0 10px rgba(0, 255, 127, 0.3);
  animation: typing 1s steps(20) forwards;
  overflow: hidden;
  white-space: nowrap;
  width: 0;
}

@keyframes typing {
  from {
    width: 0;
  }
  to {
    width: 100%;
  }
}

.user-info {
  color: var(--secondary-green);
  font-size: 14px;
}

.label {
  opacity: 0.7;
  margin-right: 8px;
}

.value {
  font-weight: 600;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.card {
  background: rgba(0, 0, 0, 0.6);
  border: 1px solid rgba(0, 255, 127, 0.2);
  border-radius: 6px;
  overflow: hidden;
  transition: all 0.3s;
  animation: slideUp 0.5s ease backwards;
}

.card:nth-child(1) { animation-delay: 0.1s; }
.card:nth-child(2) { animation-delay: 0.2s; }
.card:nth-child(3) { animation-delay: 0.3s; }

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.card:hover {
  border-color: rgba(0, 255, 127, 0.4);
  box-shadow: 0 0 20px rgba(0, 255, 127, 0.1);
  transform: translateY(-4px);
}

.card-header {
  background: rgba(0, 255, 127, 0.05);
  padding: 12px 16px;
  color: var(--primary-green);
  font-weight: 600;
  font-size: 14px;
  border-bottom: 1px solid rgba(0, 255, 127, 0.1);
}

.card-body {
  padding: 16px;
}

.stat-line {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  color: rgba(0, 255, 127, 0.8);
  font-size: 13px;
}

.stat-label {
  opacity: 0.7;
}

.stat-value {
  font-weight: 600;
}

.stat-value.online {
  color: #00ff88;
}

.action-link {
  display: block;
  padding: 10px 12px;
  margin: 8px 0;
  color: rgba(0, 255, 127, 0.8);
  text-decoration: none;
  border-left: 2px solid transparent;
  transition: all 0.2s;
}

.action-link:hover {
  color: var(--primary-green);
  background: rgba(0, 255, 127, 0.05);
  border-left-color: var(--primary-green);
  padding-left: 16px;
}

.placeholder-text {
  color: rgba(0, 255, 127, 0.4);
  font-style: italic;
  text-align: center;
  padding: 20px;
}
</style>
