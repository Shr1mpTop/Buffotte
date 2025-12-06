<template>
  <TerminalWindow title="user@buffotte:~/register">
    <div class="register-console">
      <div class="prompt">$ register</div>
      <form class="form" @submit.prevent="onRegister">
        <input v-model="form.username" class="input" type="text" placeholder="用户名" required autocomplete="username" />
        <input v-model="form.email" class="input" type="email" placeholder="邮箱" required autocomplete="email" />
        <input v-model="form.password" class="input" type="password" placeholder="密码" required autocomplete="new-password" />
        <button class="btn" type="submit">创建用户</button>
      </form>
      <div class="alt">已有账号？ <router-link to="/login">登录</router-link></div>
    </div>
  </TerminalWindow>
</template>

<script>
import TerminalWindow from '../components/TerminalWindow.vue'
import api from '../services/api'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

export default {
  name: 'Register',
  components: { TerminalWindow },
  setup() {
    const form = ref({ username: '', email: '', password: '' })
    const router = useRouter()
    const onRegister = async () => {
      const res = await api.register({ username: form.value.username, email: form.value.email, password: form.value.password })
      if (res.success) { alert('注册成功'); router.push('/login') }
      else { let msg = res.error?.detail || res.error?.message || res.error || '注册失败'; alert(msg) }
    }
    return { form, onRegister }
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
