import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Login from '@/views/Login.vue'
import Dashboard from '@/views/Dashboard.vue'
import SkillSelection from '@/views/SkillSelection.vue'
import LearningSession from '@/views/LearningSession.vue'
import KatexTest from '@/views/KatexTest.vue'

const routes = [
    { path: '/login', name: 'Login', component: Login, name: 'login' },
    { path: '/skills', name: 'SkillSelection', component: SkillSelection, meta: { requiresAuth: true } },
    { path: '/session', name: 'LearningSession', component: LearningSession, meta: { requiresAuth: true } },
    { path: '/dashboard', name: 'Dashboard', component: Dashboard, meta: { requiresAuth: true } },
    { path: '/katex-test', name: 'KatexTest', component: KatexTest },
    { path: '/', redirect: '/login' }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

router.beforeEach((to, from, next) => {
    const auth = useAuthStore()
    const isAuthenticated = auth.isLoggedIn || !!localStorage.getItem('token')
    
    if (to.meta.requiresAuth && !isAuthenticated) {
        return next({ path: '/login' })
    } else if (to.name === 'login' && isAuthenticated){
        return next({ path: '/dashboard' })
    }
    next()
})

export default router
