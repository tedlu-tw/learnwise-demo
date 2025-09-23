import { createRouter, createWebHistory } from 'vue-router'
import Login from '@/views/Login.vue'
import Dashboard from '@/views/Dashboard.vue'
import SkillSelection from '@/views/SkillSelection.vue'
import LearningSession from '@/views/LearningSession.vue'

const routes = [
  { path: '/login', name: 'Login', component: Login },
  { path: '/skills', name: 'SkillSelection', component: SkillSelection, meta: { requiresAuth: true } },
  { path: '/session', name: 'LearningSession', component: LearningSession, meta: { requiresAuth: true } },
  { path: '/dashboard', name: 'Dashboard', component: Dashboard, meta: { requiresAuth: true } },
  { path: '/', redirect: '/dashboard' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
    const isAuthenticated = !!localStorage.getItem('token')
    if (to.meta.requiresAuth && !isAuthenticated) {
        return next({ path: '/login' })
    }
  next()
})

export default router
