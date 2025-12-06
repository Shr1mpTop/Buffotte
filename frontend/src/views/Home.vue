<template>
  <div class="home">
    <header>
      <h1>首页</h1>
      <nav>
        <router-link to="/profile">Profile</router-link>
        <button @click="logout">注销</button>
      </nav>
    </header>
    <main>
      <h2>欢迎回来！</h2>
      <p>这是您的首页。</p>
    </main>
  </div>
</template>

<script>
import { useRouter } from 'vue-router'

export default {
  name: 'Home',
  setup() {
    const router = useRouter()

    const logout = () => {
      localStorage.removeItem('user')
      router.push('/login')
    }

    return {
      logout
    }
  }
}
</script>

<style scoped>
.home {
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