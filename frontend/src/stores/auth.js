import { defineStore } from 'pinia'
import { authService } from '@/services/auth.service'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: null,
    error: null
  }),
  getters: {
    currentUser: (state) => state.user,
    isLoggedIn: (state) => !!state.token
  },
  actions: {
    async login(credentials) {
      try {
        const data = await authService.login(credentials)
        this.token = data.access_token
        this.user = data.user
        this.error = null
        // Store both token and user data in localStorage
        localStorage.setItem('token', data.access_token)
        localStorage.setItem('user', JSON.stringify(data.user))
      } catch (e) {
        this.error = e.response?.data?.error || 'Login failed'
        this.user = null
        this.token = null
        localStorage.removeItem('token')
        localStorage.removeItem('user')
      }
    },
    async initializeAuth() {
      const token = localStorage.getItem('token')
      const userData = localStorage.getItem('user')
      
      if (token && userData) {
        try {
          this.token = token
          this.user = JSON.parse(userData)
          console.log('Auth initialized from localStorage:', this.user)
          
          // Optionally verify token is still valid with backend
          // If this fails, it will be handled by axios interceptor
          await authService.getCurrentUser()
        } catch (e) {
          console.error('Token verification failed:', e)
          // Token is invalid, clear everything
          this.logout()
        }
      }
    },
    logout() {
      this.user = null
      this.token = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }
})
