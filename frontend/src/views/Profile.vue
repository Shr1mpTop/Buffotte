<template>
  <TerminalWindow title="user@buffotte:~/profile">
    <div class="profile-console">
      <div class="line">欢迎回来，<strong>{{ user?.username }}</strong></div>
      <div class="line">邮箱: {{ user?.email }}</div>
      <div class="actions">
        <button class="btn" @click="logout">登出</button>
        <router-link class="btn" to="/">返回主页</router-link>
      </div>
    </div>
  </TerminalWindow>
</template>

<script>
import TerminalWindow from '../components/TerminalWindow.vue'
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

export default {
  name: 'Profile',
  components: { TerminalWindow },
  setup () {
    const user = ref(null)
    const router = useRouter()
    onMounted(() => {
      try { user.value = JSON.parse(localStorage.getItem('user')) } catch (e) {}
      if (!user.value) router.push('/login')
    })
    const logout = () => { localStorage.removeItem('user'); router.push('/login') }
    return { user, logout }
  }
}
</script>

<style scoped>
.line { margin: 8px 0 }
.actions { margin-top:12px; display:flex; gap:8px }
.btn { padding:8px 12px; border-radius:6px; background:linear-gradient(45deg,var(--primary-green),var(--secondary-green)); border:none }
</style>
