<template>
  <TerminalWindow title="user@buffotte:~/login">
    <div class="login-console">
      <div class="prompt">$ login</div>
      <form class="form" @submit.prevent="onLogin">
        <input v-model="form.email" class="input" type="email" placeholder="邮箱" required autocomplete="email" />
        <input v-model="form.password" class="input" type="password" placeholder="密码" required autocomplete="current-password" />
        <button class="btn" type="submit">登录</button>
      </form>
      <div class="alt">没有账号？ <router-link to="/register">注册</router-link></div>
    </div>
  </TerminalWindow>
</template>

<script>
import TerminalWindow from '../components/TerminalWindow.vue'
import api from '../services/api'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

export default {
  name: 'Login',
  components: { TerminalWindow },
  setup() {
    const form = ref({ email: '', password: '' })
    const router = useRouter()
    const onLogin = async () => {
      const res = await api.login(form.value)
      if (res.success) {
        localStorage.setItem('user', JSON.stringify(res.data.user));
        alert('登录成功'); router.push('/home')
      } else {
        let msg = res.error?.detail || res.error?.message || res.error || '登录失败'
        alert(msg)
      }
    }
    return { form, onLogin }
  }
}
</script>

<style scoped>
.prompt { color: var(--secondary-green); font-weight:700 }
.form { display:flex; flex-direction:column; gap:8px }
.input { background:transparent; border:1px solid rgba(0,255,127,0.08); padding:10px; color:var(--primary-green); border-radius:6px }
.btn { padding:10px; background:linear-gradient(45deg,var(--primary-green),var(--secondary-green)); color:#000; border:none; border-radius:6px; cursor:pointer }
.alt { color: rgba(159,255,191,0.6) }
</style>
