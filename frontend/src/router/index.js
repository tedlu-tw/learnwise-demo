import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'
import Dashboard from '@/views/Dashboard.vue'
import SkillSelection from '@/views/SkillSelection.vue'
import LearningSession from '@/views/LearningSession.vue'
import KatexTest from '@/views/KatexTest.vue'

const routes = [
    { path: '/login', name: 'Login', component: Login },
    { path: '/register', name: 'Register', component: Register },
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

router.beforeEach(async (to, from, next) => {
    const auth = useAuthStore()
    const isAuthenticated = auth.isLoggedIn || !!localStorage.getItem('token')

    // Handle authentication routes
    if (to.meta.requiresAuth && !isAuthenticated) {
        return next({ path: '/login' })
    }
    
    if (to.name === 'login' && isAuthenticated) {
        return next({ path: '/dashboard' })
    }

    // Initialize auth if needed
    if (isAuthenticated && !auth.user) {
        await auth.initializeAuth()
    }

    // Special handling for learning session routes
    if (to.name === 'LearningSession') {
        // If no skills selected, redirect to skill selection
        if (!auth.user?.selected_skills?.length) {
            console.log('No skills selected, redirecting to skills page')
            return next({ path: '/skills' })
        }
    }

    next()
})

export default router
