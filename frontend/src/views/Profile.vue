<template>
  <div class="profile">
    <div class="profile-header">
      <h1 class="title">$ cat ~/.profile</h1>
    </div>
    <div class="profile-content">
      <div class="info-card">
        <div class="info-row">
          <span class="label">USERNAME:</span>
          <span class="value">{{ user?.username || 'N/A' }}</span>
        </div>
        <div class="info-row">
          <span class="label">EMAIL:</span>
          <span class="value">{{ user?.email || 'N/A' }}</span>
        </div>
        <div class="info-row">
          <span class="label">STATUS:</span>
          <span class="value active">● ACTIVE</span>
        </div>
        <div class="info-row">
          <span class="label">REGISTERED DAYS:</span>
          <span class="value">{{ daysRegistered }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

export default {
  name: 'Profile',
  setup () {
    const user = ref(null)
    const daysRegistered = ref(0)
    const router = useRouter()
    onMounted(async () => {
      try { user.value = JSON.parse(localStorage.getItem('user')) } catch (e) {}
      if (!user.value) router.push('/login')
      else {
        // 获取注册天数
        try {
          const response = await axios.get(`http://localhost:8000/api/user/profile?email=${user.value.email}`)
          const createdAt = new Date(response.data.created_at)
          const now = new Date()
          const diffTime = Math.abs(now - createdAt)
          daysRegistered.value = Math.floor(diffTime / (1000 * 60 * 60 * 24)) + 1
        } catch (error) {
          console.error('获取注册天数失败:', error)
          daysRegistered.value = 0
        }
      }
    })
    return { user, daysRegistered }
  }
}
</script>

<style scoped>
.profile {
  width: 100%;
  max-width: 800px;
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

.profile-header {
  margin-bottom: 32px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(0, 255, 127, 0.2);
}

.title {
  color: var(--primary-green);
  font-size: 24px;
  font-weight: 700;
  margin: 0;
  text-shadow: 0 0 10px rgba(0, 255, 127, 0.3);
}

.info-card {
  background: rgba(0, 0, 0, 0.6);
  border: 1px solid rgba(0, 255, 127, 0.2);
  border-radius: 6px;
  padding: 24px;
}

.info-row {
  display: flex;
  padding: 12px 0;
  border-bottom: 1px solid rgba(0, 255, 127, 0.1);
}

.info-row:last-child {
  border-bottom: none;
}

.label {
  color: rgba(0, 255, 127, 0.7);
  font-weight: 600;
  min-width: 120px;
}

.value {
  color: var(--primary-green);
  flex: 1;
}

.value.active {
  color: #00ff88;
}
</style>
