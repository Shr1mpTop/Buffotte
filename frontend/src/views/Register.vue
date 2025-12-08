<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-header">
        <div class="logo">BUFFOTTE</div>
        <div class="subtitle">用户认证系统</div>
      </div>
      <div class="auth-card">
        <div class="card-title">$ register</div>
        <form class="auth-form" @submit.prevent="onRegister">
          <div class="form-group">
            <label class="form-label">用户名</label>
            <input v-model="form.username" class="form-input" type="text" placeholder="username" required autocomplete="username" />
          </div>
          <div class="form-group">
            <label class="form-label">邮箱地址</label>
            <input v-model="form.email" class="form-input" type="email" placeholder="user@example.com" required autocomplete="email" />
          </div>
          <div class="form-group">
            <label class="form-label">密码</label>
            <input v-model="form.password" class="form-input" type="password" placeholder="••••••••" required autocomplete="new-password" />
          </div>
          <button class="submit-btn" type="submit">创建账号</button>
        </form>
        <div class="auth-footer">
          <span class="hint">已有账号？</span>
          <router-link to="/login" class="link">立即登录</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../services/api'
import { useToast } from '../composables/useToast'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

export default {
  name: 'Register',
  setup() {
    const form = ref({ username: '', email: '', password: '' })
    const router = useRouter()
    const { success, error } = useToast()
    
    const onRegister = async () => {
      const res = await api.register({ username: form.value.username, email: form.value.email, password: form.value.password })
      if (res.success) { 
        success('注册成功')
        setTimeout(() => router.push('/login'), 500)
      }
      else { 
        let msg = res.error?.detail || res.error?.message || res.error || '注册失败'
        error(msg)
      }
    }
    return { form, onRegister }
  }
}
</script>

<style scoped>
.auth-container{width:100%;max-width:420px;animation:fadeInUp .5s ease}
@keyframes fadeInUp{from{opacity:0;transform:translateY(30px)}
to{opacity:1;transform:translateY(0)}
}
.auth-header{text-align:center;margin-bottom:32px}
.logo{color:var(--primary-green);font-size:32px;font-weight:700;letter-spacing:4px;text-shadow:0 0 20px rgba(0,255,127,.5);margin-bottom:8px;animation:glow 2s ease-in-out infinite}
@keyframes glow{0%,100%{text-shadow:0 0 20px rgba(0,255,127,.5)}
50%{text-shadow:0 0 30px rgba(0,255,127,.8),0 0 40px rgba(0,255,127,.4)}
}
.subtitle{color:var(--secondary-green);font-size:14px;opacity:.7}
.auth-card{background:rgba(0,0,0,.8);border:1px solid rgba(0,255,127,.2);border-radius:8px;padding:32px;box-shadow:0 0 40px rgba(0,255,127,.1)}
.card-title{color:var(--primary-green);font-size:18px;font-weight:600;margin-bottom:24px;padding-bottom:12px;border-bottom:1px solid rgba(0,255,127,.1)}
.auth-form{margin-bottom:20px}
.form-group{margin-bottom:20px}
.form-label{display:block;color:rgba(0,255,127,.7);font-size:13px;margin-bottom:8px;font-weight:500}
.form-input{width:100%;background:rgba(0,255,127,.05);border:1px solid rgba(0,255,127,.2);padding:12px 16px;color:var(--primary-green);border-radius:6px;font-family:'Source Code Pro',monospace;font-size:14px;transition:all .2s}
.form-input:focus{outline:0;border-color:var(--primary-green);background:rgba(0,255,127,.08);box-shadow:0 0 10px rgba(0,255,127,.2)}
.form-input::placeholder{color:rgba(0,255,127,.3)}
.submit-btn{width:100%;padding:14px;background:linear-gradient(45deg,var(--primary-green),var(--secondary-green));color:#000;border:none;border-radius:6px;font-weight:600;font-size:15px;cursor:pointer;transition:all .2s;font-family:'Source Code Pro',monospace}
.submit-btn:hover{transform:translateY(-2px);box-shadow:0 4px 20px rgba(0,255,127,.3)}
.auth-footer{text-align:center;padding-top:20px;border-top:1px solid rgba(0,255,127,.1)}
.hint{color:rgba(0,255,127,.5);font-size:13px}
.link{color:var(--primary-green);text-decoration:none;margin-left:8px;font-weight:500}
.link:hover{text-decoration:underline}
</style>
