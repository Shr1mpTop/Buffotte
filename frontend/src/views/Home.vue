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
        <div class="card-header">用户档案</div>
        <div class="card-body profile-card-body">
          <div>
            <div class="profile-line">
              <span class="profile-label">用户名:</span>
              <span class="profile-value">{{ user?.username || '未设置' }}</span>
            </div>
            <div class="profile-line">
              <span class="profile-label">邮箱:</span>
              <span class="profile-value">{{ user?.email || '未设置' }}</span>
            </div>
            <div class="profile-line">
              <span class="profile-label">注册时间:</span>
              <span class="profile-value">{{ formatRegistrationTime(user?.created_at) || '未设置' }}</span>
            </div>
            <div v-if="loadingDetails" class="profile-line">
                <span class="profile-label">等级:</span>
                <span class="profile-value">加载中...</span>
            </div>
            <div v-else-if="detailsError" class="profile-line">
                <span class="profile-label">等级:</span>
                <span class="profile-value error">{{ detailsError }}</span>
            </div>
            <template v-else-if="userDetails">
                <div class="profile-line">
                    <span class="profile-label">等级:</span>
                    <span class="profile-value">Lv.{{ userDetails.level }} ({{ userDetails.level_name }})</span>
                </div>
                <div class="profile-line">
                    <span class="profile-label">可追踪:</span>
                    <span class="profile-value">{{ userDetails.track_permit }} 个饰品</span>
                </div>
            </template>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="card-header">快速操作</div>
        <div class="card-body">
          <!-- 移除了指向 /profile 的链接 -->
          <router-link to="/kline" class="action-link">→ K线数据</router-link>
          <router-link to="/news" class="action-link">→ 查看资讯</router-link>
          <router-link to="/tracking" class="action-link">→ 管理追踪</router-link>
        </div>
      </div>
      <div class="card">
        <div class="card-header">数据面板</div>
        <div class="card-body">
            <div v-if="loadingDetails" class="placeholder-text">加载中...</div>
            <div v-else-if="detailsError" class="placeholder-text error">{{ detailsError }}</div>
            <div v-else-if="userDetails" class="stat-line">
                <span class="stat-label">▸ 已追踪饰品:</span>
                <span class="stat-value">{{ userDetails.tracked_count }} / {{ userDetails.track_permit }}</span>
            </div>
            <div v-else class="placeholder-text">[占位区域]</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import BootAnimation from '../components/BootAnimation.vue'
import { ref, onMounted, onUnmounted } from 'vue'
import { client } from '../services/api'
import { useToast } from '../composables/useToast'

export default {
  name: 'Dashboard',
  components: { BootAnimation },
  setup() {
    const user = ref(null)
    const sessionTime = ref('00:00:00')
    const showBoot = ref(false)
    const userDetails = ref(null)
    const loadingDetails = ref(false)
    const detailsError = ref(null)
    let startTime = Date.now()
    let timer = null

    const updateSessionTime = () => {
      const elapsed = Math.floor((Date.now() - startTime) / 1000)
      const h = Math.floor(elapsed / 3600).toString().padStart(2, '0')
      const m = Math.floor((elapsed % 3600) / 60).toString().padStart(2, '0')
      const s = (elapsed % 60).toString().padStart(2, '0')
      sessionTime.value = `${h}:${m}:${s}`
    }

    const formatRegistrationTime = (timestamp) => {
      if (!timestamp) return ''
      const createdDate = new Date(timestamp)
      const now = new Date()
      const diffTime = now - createdDate
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
      return `注册 ${diffDays} 天`
    }

    onMounted(async () => {
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

      // 获取用户详细信息
      if (user.value?.email) {
        loadingDetails.value = true
        detailsError.value = null
        try {
          const response = await client.get(`/user/details/${user.value.email}`)
          userDetails.value = response.data
        } catch (e) {
          console.error('获取用户详情失败:', e)
          detailsError.value = '获取失败'
        } finally {
          loadingDetails.value = false
        }
      }
    })

    onUnmounted(() => {
      if (timer) clearInterval(timer)
    })

    return { user, sessionTime, showBoot, formatRegistrationTime, userDetails, loadingDetails, detailsError }
  }
}
</script>

<style scoped>
.dashboard{width:100%;max-width:1200px;padding:24px;margin:40px 0 0 0;animation:fadeIn .4s ease}
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
.dashboard-header{margin-bottom:24px;padding-bottom:16px;border-bottom:1px solid rgba(0,255,127,.2)}
.title{color:var(--primary-green);font-size:24px;font-weight:700;margin:0 0 12px 0;text-shadow:0 0 10px rgba(0,255,127,.3);animation:typing 1s steps(20) forwards;overflow:hidden;white-space:nowrap;width:0}
@keyframes typing{from{width:0}
to{width:100%}
}
.user-info{color:var(--secondary-green);font-size:14px}
.label{opacity:.7;margin-right:8px}
.value{font-weight:600}
.dashboard-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px}
.card{background:rgba(0,0,0,.6);border:1px solid rgba(0,255,127,.2);border-radius:6px;overflow:hidden;transition:all .3s;animation:slideUp .5s ease backwards}
.card:first-child{animation-delay:.1s}
.card:nth-child(2){animation-delay:.2s}
.card:nth-child(3){animation-delay:.3s}

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
  margin-bottom: 8px;
  font-size: 13px;
}

.stat-label {
  color: var(--secondary-green);
  opacity: 0.8;
}

.stat-value {
  color: var(--primary-green);
  font-weight: 500;
}

.stat-value.online {
  color: #00ff8b;
  text-shadow: 0 0 8px rgba(0, 255, 139, 0.5);
}

.action-link {
  display: block;
  color: var(--primary-green);
  text-decoration: none;
  padding: 8px 0;
  transition: color 0.2s, transform 0.2s;
  font-size: 13px;

  &:hover {
    color: #00cc66;
    transform: translateX(5px);
    text-shadow: 0 0 8px rgba(0, 204, 102, 0.3);
  }
}

.profile-card-body {
  padding: 16px;
}

.profile-line {
  display: flex;
  margin-bottom: 8px;
  font-size: 13px;
  align-items: center;
}

.profile-label {
  color: var(--secondary-green);
  opacity: 0.8;
  width: 60px; /* 固定标签宽度 */
  flex-shrink: 0;
}

.profile-value {
  color: var(--primary-green);
  font-weight: 500;
  flex-grow: 1;
  word-break: break-all;
}

.profile-value.error {
  color: #ff6b6b;
  font-weight: bold;
}

.profile-action {
  margin-top: 15px;
  border-top: 1px dashed rgba(0, 255, 127, 0.1);
  padding-top: 15px;
  text-align: center;
}

.action-button {
  background: rgba(0, 255, 127, 0.1);
  border: 1px solid var(--primary-green);
  color: var(--primary-green);
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: 'Source Code Pro', monospace;
  font-size: 13px;

  &:hover {
    background: var(--primary-green);
    color: #0a0e0a;
    box-shadow: 0 0 15px rgba(0, 255, 127, 0.6);
    transform: translateY(-2px);
  }
}

.placeholder-text {
  color: var(--secondary-green);
  opacity: 0.5;
  text-align: center;
  padding: 20px;
  font-size: 14px;
}

.placeholder-text.error {
  color: #ff6b6b;
  font-weight: bold;
}
</style>
