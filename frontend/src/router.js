import { createRouter, createWebHistory } from 'vue-router'
import Login from './views/Login.vue'
import Register from './views/Register.vue'
import MainLayout from './layouts/MainLayout.vue'
import Home from './views/Home.vue'
import Kline from './views/Kline.vue'
import NewsView from './views/NewsView.vue'

const routes = [
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  { 
    path: '/', 
    component: MainLayout,
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', component: Home, alias: '/home' },
      { path: 'kline', component: Kline },
      { path: 'news', component: NewsView }
    ]
  }
]

const router = createRouter({ history: createWebHistory(), routes })
export default router
