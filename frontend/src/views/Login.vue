<template>
  <div class="login">
    <h2>登录</h2>
    <form @submit.prevent="login">
      <input v-model="form.email" type="email" placeholder="邮箱" required>
      <input v-model="form.password" type="password" placeholder="密码" required>
      <button type="submit">登录</button>
    </form>
    <p>没有账号？<router-link to="/register">注册</router-link></p>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

export default {
  name: 'Login',
  setup() {
    const form = ref({
      email: '',
      password: ''
    })
    const router = useRouter()

    const login = async () => {
      try {
        const response = await axios.post('http://localhost:8000/api/login', {
          email: form.value.email,
          password: form.value.password
        })
        if (response.data.success) {
          localStorage.setItem('user', JSON.stringify(response.data.user))
          router.push('/home')
        } else {
          alert(response.data.message)
        }
      } catch (error) {
        alert(error.response?.data?.detail || '登录失败')
      }
    }

    return {
      form,
      login
    }
  }
}
</script>

<style scoped>
.login {
  max-width: 400px;
  margin: 0 auto;
  padding: 20px;
}

form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

input {
  padding: 8px;
}

button {
  padding: 8px;
  background-color: #42b883;
  color: white;
  border: none;
  cursor: pointer;
}

button:hover {
  background-color: #369870;
}
</style>