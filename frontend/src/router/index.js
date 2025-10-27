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
    { path: '/skill-selection', name: 'SkillSelection', component: SkillSelection, meta: { requiresAuth: true } },
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
    const token = localStorage.getItem('token')

    // Initialize auth if we have a token but no user data
    if (token && !auth.user) {
        try {
            await auth.initializeAuth()
        } catch (error) {
            console.error('Failed to initialize auth:', error)
            // If initialization fails, clear everything and redirect to login
            auth.logout()
            return next({ path: '/login' })
        }
    }

    const isAuthenticated = auth.isLoggedIn

    // Handle authentication routes
    if (to.meta.requiresAuth && !isAuthenticated) {
        return next({ path: '/login' })
    }
    
    if (to.name === 'Login' && isAuthenticated) {
        return next({ path: '/dashboard' })
    }

    // Special handling for learning session routes
    if (to.name === 'LearningSession') {
        // If no skills selected, redirect to skill selection
        if (!auth.user?.selected_skills?.length) {
            console.log('No skills selected, redirecting to skills page')
            return next({ path: '/skill-selection' })
        }
    }

    next()
})

export default router
