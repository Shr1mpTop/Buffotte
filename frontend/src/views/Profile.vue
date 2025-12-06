<template>
  <div class="profile">
    <header>
      <h1>Profile</h1>
      <nav>
        <router-link to="/home">首页</router-link>
        <button @click="logout">注销</button>
      </nav>
    </header>
    <main>
      <h2>用户信息</h2>
      <div v-if="user">
        <p><strong>邮箱:</strong> {{ user.email }}</p>
        <p><strong>用户名:</strong> {{ user.username || '未设置' }}</p>
      </div>
      <div v-else>
        <p>未登录</p>
      </div>
    </main>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

export default {
  name: 'Profile',
  setup() {
    const user = ref(null)
    const router = useRouter()

    onMounted(() => {
      const userData = localStorage.getItem('user')
      if (userData) {
        user.value = JSON.parse(userData)
      } else {
        router.push('/login')
      }
    })

    const logout = () => {
      localStorage.removeItem('user')
      router.push('/login')
    }

    return {
      user,
      logout
    }
  }
}
</script>

<style scoped>
.profile {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #ccc;
  padding-bottom: 10px;
}

nav {
  display: flex;
  gap: 10px;
  align-items: center;
}

button {
  padding: 5px 10px;
  background-color: #f44336;
  color: white;
  border: none;
  cursor: pointer;
}

button:hover {
  background-color: #d32f2f;
}
</style>