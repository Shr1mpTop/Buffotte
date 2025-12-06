<template>
  <div class="register">
    <h2>注册</h2>
    <form @submit.prevent="register">
      <input v-model="form.username" type="text" placeholder="用户名" required>
      <input v-model="form.email" type="email" placeholder="邮箱" required>
      <input v-model="form.password" type="password" placeholder="密码" required>
      <button type="submit">注册</button>
    </form>
    <p>已有账号？<router-link to="/login">登录</router-link></p>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

export default {
  name: 'Register',
  setup() {
    const form = ref({
      username: '',
      email: '',
      password: ''
    })
    const router = useRouter()

    const register = async () => {
      try {
        const response = await axios.post('http://localhost:8000/api/register', {
          username: form.value.username,
          email: form.value.email,
          password: form.value.password
        })
        if (response.data.success) {
          alert('注册成功！请登录')
          router.push('/login')
        } else {
          alert(response.data.message)
        }
      } catch (error) {
        alert(error.response?.data?.detail || '注册失败')
      }
    }

    return {
      form,
      register
    }
  }
}
</script>

<style scoped>
.register {
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